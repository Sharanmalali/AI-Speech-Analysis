"""Celery task that runs the full audio-analysis pipeline for a job."""

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

from app.config import settings
from app.core.logging import get_logger
from app.database.session import session_scope
from app.models import Job
from app.models.enums import JobStage, JobStatus
from app.services import job_service
from app.services.storage import get_storage
from app.tasks.celery_app import celery_app

logger = get_logger(__name__)


def _update_progress(job_id: uuid.UUID, stage: JobStage, progress: float) -> None:
    """Persist incremental progress in its own short transaction."""
    with session_scope() as db:
        job = db.get(Job, job_id)
        if job is not None:
            job_service.update_progress(db, job, stage, progress)


@celery_app.task(bind=True, name="app.tasks.process_audio_job", max_retries=0)
def process_audio_job(self, job_id: str) -> dict:  # type: ignore[no-untyped-def]
    """Download the audio, run the pipeline and persist results."""
    jid = uuid.UUID(job_id)
    logger.info("task_started", job_id=job_id, task_id=self.request.id)

    # Mark processing + fetch storage location.
    with session_scope() as db:
        job = db.get(Job, jid)
        if job is None:
            logger.error("task_job_missing", job_id=job_id)
            return {"job_id": job_id, "status": "missing"}
        job_service.mark_processing(db, job, task_id=self.request.id)
        storage_bucket = job.audio_file.storage_bucket
        storage_path = job.audio_file.storage_path
        extension = job.audio_file.extension

    tmp_path: Path | None = None
    try:
        # Materialise the audio to a local temp file for the ML stack.
        storage = get_storage()
        data = storage.download(storage_path)
        settings.UPLOAD_TMP_DIR.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(
            suffix=f".{extension}", dir=str(settings.UPLOAD_TMP_DIR)
        )
        tmp_path = Path(tmp_name)
        with open(fd, "wb") as fh:
            fh.write(data)

        # Import the pipeline lazily so the heavy ML stack is only loaded in
        # the worker process, never in the API process.
        from app.services.ml.pipeline import AudioAnalysisPipeline

        def progress(stage: JobStage, pct: float) -> None:
            _update_progress(jid, stage, pct)

        result = AudioAnalysisPipeline(progress=progress).run(tmp_path)

        with session_scope() as db:
            job = db.get(Job, jid)
            job_service.persist_result(db, job, result)

        logger.info("task_completed", job_id=job_id, speakers=result.detected_speakers)
        return {
            "job_id": job_id,
            "status": JobStatus.COMPLETED.value,
            "detected_speakers": result.detected_speakers,
        }

    except Exception as exc:  # noqa: BLE001
        logger.exception("task_failed", job_id=job_id, error=str(exc))
        with session_scope() as db:
            job = db.get(Job, jid)
            if job is not None:
                job_service.mark_failed(db, job, error=str(exc))
        return {"job_id": job_id, "status": JobStatus.FAILED.value, "error": str(exc)}

    finally:
        if tmp_path is not None and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
