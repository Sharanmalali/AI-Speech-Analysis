"""Audio file schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel

from app.schemas.common import TimestampedSchema


class AudioFileRead(TimestampedSchema):
    id: uuid.UUID
    original_filename: str
    content_type: str
    extension: str
    size_bytes: int
    duration_seconds: float | None
    sample_rate: int | None
    channels: int | None


class AudioUploadResponse(BaseModel):
    """Returned immediately after a successful upload + job creation."""

    audio_file_id: uuid.UUID
    job_id: uuid.UUID
    status: str
    message: str = "Upload accepted. Processing has been queued."
