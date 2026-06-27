"""Upload validation and file helpers.

Performs defence-in-depth validation of uploaded audio: extension allow-list,
declared content-type allow-list, size limit and a magic-byte sniff so a
mismatched/forged extension is rejected before the file ever reaches the
processing pipeline.
"""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

from app.config import settings
from app.core.exceptions import FileValidationError

# Leading magic bytes for the audio containers we accept. ``None`` means the
# format has no reliable fixed signature at offset 0 (validated by extension +
# content-type + successful decode instead).
_MAGIC_SIGNATURES: dict[str, list[bytes]] = {
    "wav": [b"RIFF"],
    "ogg": [b"OggS"],
    "flac": [b"fLaC"],
    "mp3": [b"ID3", b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"],
    "aac": [b"\xff\xf1", b"\xff\xf9", b"ADIF"],
    # m4a/mp4: 'ftyp' box appears at byte offset 4.
    "m4a": [],
}


def get_extension(filename: str) -> str:
    return Path(filename).suffix.lower().lstrip(".")


def validate_extension(filename: str) -> str:
    ext = get_extension(filename)
    if ext not in settings.ALLOWED_AUDIO_EXTENSIONS:
        raise FileValidationError(
            f"Unsupported file extension '.{ext}'.",
            code="unsupported_extension",
            details={"allowed": settings.ALLOWED_AUDIO_EXTENSIONS},
        )
    return ext


def validate_content_type(content_type: str | None) -> None:
    if content_type and content_type.lower() not in settings.ALLOWED_AUDIO_MIME_TYPES:
        raise FileValidationError(
            f"Unsupported content type '{content_type}'.",
            code="unsupported_content_type",
            details={"allowed": settings.ALLOWED_AUDIO_MIME_TYPES},
        )


def validate_size(size_bytes: int) -> None:
    if size_bytes <= 0:
        raise FileValidationError("Uploaded file is empty.", code="empty_file")
    if size_bytes > settings.max_upload_size_bytes:
        raise FileValidationError(
            f"File exceeds the maximum size of {settings.MAX_UPLOAD_SIZE_MB} MB.",
            code="file_too_large",
            details={"max_mb": settings.MAX_UPLOAD_SIZE_MB},
        )


def sniff_magic_bytes(head: bytes, ext: str) -> None:
    """Validate the file header matches the declared extension."""
    # mp4/m4a: check for 'ftyp' box at offset 4.
    if ext == "m4a":
        if len(head) >= 12 and head[4:8] == b"ftyp":
            return
        raise FileValidationError(
            "File header does not match an MP4/M4A container.", code="magic_mismatch"
        )

    signatures = _MAGIC_SIGNATURES.get(ext, [])
    if not signatures:
        return  # nothing to check for this format
    if any(head.startswith(sig) for sig in signatures):
        return
    raise FileValidationError(
        f"File header does not match the '.{ext}' format.", code="magic_mismatch"
    )


def sha256_hexdigest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def generate_storage_path(user_id: uuid.UUID | str, original_filename: str) -> str:
    """Build a collision-resistant object-storage key."""
    ext = get_extension(original_filename)
    unique = uuid.uuid4().hex
    return f"{user_id}/{unique}.{ext}"


def human_readable_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"
