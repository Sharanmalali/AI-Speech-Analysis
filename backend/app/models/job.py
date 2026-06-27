"""Job ORM model — a single audio-analysis pipeline run."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import JobStage, JobStatus

if TYPE_CHECKING:
    from app.models.audio_file import AudioFile
    from app.models.report import Report
    from app.models.speaker import Speaker
    from app.models.user import User


class Job(Base, UUIDMixin, TimestampMixin):
    """Tracks the lifecycle and progress of an audio processing pipeline run."""

    __tablename__ = "jobs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    audio_file_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("audio_files.id", ondelete="CASCADE"), index=True, nullable=False
    )

    # Celery task id for cancellation / status correlation.
    task_id: Mapped[str | None] = mapped_column(String(64), index=True)

    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status", native_enum=False, length=20),
        default=JobStatus.PENDING,
        nullable=False,
        index=True,
    )
    stage: Mapped[JobStage] = mapped_column(
        Enum(JobStage, name="job_stage", native_enum=False, length=40),
        default=JobStage.UPLOADED,
        nullable=False,
    )
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Aggregated summary.
    detected_speakers: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    processing_time_seconds: Mapped[float | None] = mapped_column(Float)

    # --- Relationships -------------------------------------------------------
    user: Mapped["User"] = relationship(back_populates="jobs")
    audio_file: Mapped["AudioFile"] = relationship(back_populates="jobs")
    speakers: Mapped[list["Speaker"]] = relationship(
        back_populates="job", cascade="all, delete-orphan", order_by="Speaker.label"
    )
    report: Mapped["Report | None"] = relationship(
        back_populates="job", cascade="all, delete-orphan", uselist=False
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Job id={self.id} status={self.status.value} stage={self.stage.value}>"
