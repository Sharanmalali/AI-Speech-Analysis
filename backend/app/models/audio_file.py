"""AudioFile ORM model — metadata for an uploaded recording."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.job import Job
    from app.models.user import User


class AudioFile(Base, UUIDMixin, TimestampMixin):
    """An uploaded audio recording stored in Supabase Storage."""

    __tablename__ = "audio_files"

    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    extension: Mapped[str] = mapped_column(String(16), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    # Object storage location.
    storage_bucket: Mapped[str] = mapped_column(String(128), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)

    # Audio metadata (populated after probing).
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    sample_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    channels: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # SHA-256 checksum for integrity / dedup.
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), index=True)

    # --- Relationships -------------------------------------------------------
    owner: Mapped["User"] = relationship(back_populates="audio_files")
    jobs: Mapped[list["Job"]] = relationship(
        back_populates="audio_file", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AudioFile id={self.id} name={self.original_filename}>"
