"""User ORM model."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import UserRole

if TYPE_CHECKING:
    from app.models.audio_file import AudioFile
    from app.models.audit_log import AuditLog
    from app.models.job import Job


class User(Base, UUIDMixin, TimestampMixin):
    """Application user.

    Authentication is delegated to Supabase Auth; ``supabase_uid`` links this
    local profile row to the Supabase identity. ``hashed_password`` is only
    populated for users created via the local email/password fallback flow.
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Link to the Supabase Auth identity (nullable for local-only accounts).
    supabase_uid: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)

    # Local credential fallback (optional when Supabase Auth is the source).
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=False, length=20),
        default=UserRole.USER,
        nullable=False,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # --- Relationships -------------------------------------------------------
    audio_files: Mapped[list["AudioFile"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    jobs: Mapped[list["Job"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="user")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} email={self.email} role={self.role.value}>"
