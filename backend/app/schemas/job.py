"""Job schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import JobStage, JobStatus
from app.schemas.audio import AudioFileRead
from app.schemas.common import TimestampedSchema


class JobRead(TimestampedSchema):
    id: uuid.UUID
    audio_file_id: uuid.UUID
    status: JobStatus
    stage: JobStage
    progress: float
    detected_speakers: int | None
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    processing_time_seconds: float | None


class JobWithAudio(JobRead):
    audio_file: AudioFileRead


class JobStatusResponse(BaseModel):
    """Lightweight polling payload for the processing screen."""

    id: uuid.UUID
    status: JobStatus
    stage: JobStage
    progress: float
    detected_speakers: int | None = None
    error_message: str | None = None
