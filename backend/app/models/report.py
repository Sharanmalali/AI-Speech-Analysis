"""Report ORM model — generated PDF report metadata."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.job import Job


class Report(Base, UUIDMixin, TimestampMixin):
    """Metadata + storage location for a generated PDF report."""

    __tablename__ = "reports"

    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), index=True, nullable=False, unique=True
    )

    storage_bucket: Mapped[str] = mapped_column(String(128), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # --- Relationships -------------------------------------------------------
    job: Mapped["Job"] = relationship(back_populates="report")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Report id={self.id} job_id={self.job_id}>"
