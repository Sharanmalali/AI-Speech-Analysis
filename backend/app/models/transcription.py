"""Transcription ORM model — a timestamped speech segment."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.speaker import Speaker


class Transcription(Base, UUIDMixin, TimestampMixin):
    """A single timestamped utterance segment for a speaker.

    Stores both the original Kannada transcription and its English
    translation so the UI/report can show either.
    """

    __tablename__ = "transcriptions"

    speaker_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("speakers.id", ondelete="CASCADE"), index=True, nullable=False
    )

    start_time: Mapped[float] = mapped_column(Float, nullable=False)  # seconds
    end_time: Mapped[float] = mapped_column(Float, nullable=False)    # seconds

    text_source: Mapped[str | None] = mapped_column(Text, nullable=True)   # Kannada
    text_translated: Mapped[str | None] = mapped_column(Text, nullable=True)  # English

    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # --- Relationships -------------------------------------------------------
    speaker: Mapped["Speaker"] = relationship(back_populates="transcriptions")

    @property
    def duration(self) -> float:
        return max(0.0, self.end_time - self.start_time)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Transcription {self.start_time:.1f}-{self.end_time:.1f}s>"
