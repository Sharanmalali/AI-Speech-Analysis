"""Audio upload endpoint.

Validates the uploaded file (extension, content-type, size, magic bytes),
streams it to object storage, records the ``AudioFile`` + ``Job`` rows and
enqueues the background processing task. Heavily rate-limited.
"""

from fastapi import APIRouter, Depends, File, Request, Response, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.core.exceptions import AuthorizationError, FileValidationError, NotFoundError
from app.core.logging import get_logger
from app.core.rate_limit import limiter
from app.database import get_db
from app.dependencies import client_ip, get_current_user
from app.models import AudioFile, User
from app.models.enums import AuditAction, UserRole
from app.schemas.audio import AudioUploadResponse
from app.services import auth_service, job_service
from app.services.storage import get_storage
from app.tasks.dispatch import enqueue_audio_job
from app.utils import files as file_utils
from app.utils.audio import probe
import uuid

logger = get_logger(__name__)

router = APIRouter(prefix="/audio", tags=["audio"])

_MAGIC_HEAD_BYTES = 32


@router.post(
    "/upload",
    response_model=AudioUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload a conversation audio file for analysis",
)
@limiter.limit(settings.RATE_LIMIT_UPLOAD)
async def upload_audio(
    request: Request,
    response: Response,
    file: UploadFile = File(..., description="Audio file (wav, mp3, aac, ogg, m4a, flac)"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AudioUploadResponse:
    # --- Validate filename / extension / declared content type --------------
    if not file.filename:
        raise FileValidationError("A filename is required.", code="missing_filename")
    ext = file_utils.validate_extension(file.filename)
    file_utils.validate_content_type(file.content_type)

    # --- Read + validate size + magic bytes ---------------------------------
    data = await file.read()
    file_utils.validate_size(len(data))
    file_utils.sniff_magic_bytes(data[:_MAGIC_HEAD_BYTES], ext)

    checksum = file_utils.sha256_hexdigest(data)
    storage_path = file_utils.generate_storage_path(user.id, file.filename)
    content_type = file.content_type or f"audio/{ext}"

    # --- Persist to object storage ------------------------------------------
    storage = get_storage()
    storage.upload(storage_path, data, content_type)

    # --- Probe metadata (best-effort) ---------------------------------------
    duration = sample_rate = channels = None
    try:
        # Prefer a local backend path; otherwise probe the uploaded bytes via a
        # short-lived temp file (e.g. Supabase storage exposes no local path),
        # so duration is captured at upload time regardless of the backend.
        local_path = getattr(storage, "local_path", None)
        if local_path is not None:
            meta = probe(local_path(storage_path))
        else:
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=f".{ext}") as tmp:
                tmp.write(data)
                tmp.flush()
                meta = probe(tmp.name)
        duration, sample_rate, channels = (
            meta.duration_seconds, meta.sample_rate, meta.channels
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("probe_skipped", error=str(exc))

    audio_file = AudioFile(
        owner_id=user.id,
        original_filename=file.filename,
        content_type=content_type,
        extension=ext,
        size_bytes=len(data),
        storage_bucket=settings.SUPABASE_STORAGE_BUCKET,
        storage_path=storage_path,
        checksum_sha256=checksum,
        duration_seconds=duration,
        sample_rate=sample_rate,
        channels=channels,
    )
    db.add(audio_file)
    db.flush()

    job = job_service.create_job(db, user=user, audio_file=audio_file)

    auth_service.record_audit(
        db,
        action=AuditAction.UPLOAD_AUDIO,
        user_id=user.id,
        resource_type="audio_file",
        resource_id=str(audio_file.id),
        ip_address=client_ip(request),
        detail={"filename": file.filename, "size": len(data)},
    )

    # Commit before enqueueing so the worker can read the rows.
    db.commit()

    task_id = enqueue_audio_job(str(job.id))
    if task_id:
        job.task_id = task_id
        db.add(job)
        db.commit()

    return AudioUploadResponse(
        audio_file_id=audio_file.id,
        job_id=job.id,
        status=job.status.value,
    )


@router.get(
    "/{audio_file_id}/stream",
    summary="Stream an uploaded audio file (owner or privileged roles only)",
)
async def stream_audio(
    audio_file_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> StreamingResponse:
    audio = db.get(AudioFile, audio_file_id)
    if audio is None:
        raise NotFoundError("Audio file not found.")
    if audio.owner_id != user.id and user.role not in (UserRole.ADMIN, UserRole.DOCTOR):
        raise AuthorizationError("You do not have access to this audio file.")

    data = get_storage().download(audio.storage_path)

    def _iter():
        yield data

    return StreamingResponse(
        _iter(),
        media_type=audio.content_type,
        headers={
            "Content-Disposition": f'inline; filename="{audio.original_filename}"',
            "Accept-Ranges": "bytes",
            "Content-Length": str(len(data)),
        },
    )
