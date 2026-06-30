"""Speaker ORM model — a diarized speaker within a job."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.job import Job
    from app.models.prediction import Prediction
    from app.models.transcription import Transcription


class Speaker(Base, UUIDMixin, TimestampMixin):
    """A single speaker detected by diarization (e.g. "Speaker A")."""

    __tablename__ = "speakers"

    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), index=True, nullable=False
    )

    # Human label ("A", "B", ...) and the raw diarization id ("SPEAKER_00").
    label: Mapped[str] = mapped_column(String(16), nullable=False)
    diarization_id: Mapped[str] = mapped_column(String(64), nullable=False)

    # UI color assigned for timelines/charts (hex).
    color: Mapped[str | None] = mapped_column(String(9), nullable=True)

    # Speech statistics aggregated across the speaker's segments.
    total_speech_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_pause_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    segment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # AI-generated clinical narrative (3-4 sentences summarizing findings).
    clinical_narrative: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Relationships -------------------------------------------------------
    job: Mapped["Job"] = relationship(back_populates="speakers")
    transcriptions: Mapped[list["Transcription"]] = relationship(
        back_populates="speaker",
        cascade="all, delete-orphan",
        order_by="Transcription.start_time",
    )
    prediction: Mapped["Prediction | None"] = relationship(
        back_populates="speaker", cascade="all, delete-orphan", uselist=False
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Speaker id={self.id} label={self.label}>"
