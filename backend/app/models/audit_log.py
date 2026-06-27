"""AuditLog ORM model — immutable compliance trail."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.database.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import AuditAction

JSONType = JSON().with_variant(JSONB(), "postgresql")

if TYPE_CHECKING:
    from app.models.user import User


class AuditLog(Base, UUIDMixin, TimestampMixin):
    """Records security- and data-relevant actions for traceability."""

    __tablename__ = "audit_logs"

    # Nullable: failed logins may not resolve to a known user.
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )

    action: Mapped[AuditAction] = mapped_column(
        Enum(AuditAction, name="audit_action", native_enum=False, length=40),
        nullable=False,
        index=True,
    )
    resource_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Arbitrary structured context (never store secrets here).
    detail: Mapped[dict | None] = mapped_column(JSONType, nullable=True)

    # --- Relationships -------------------------------------------------------
    user: Mapped["User | None"] = relationship(back_populates="audit_logs")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AuditLog action={self.action.value} user_id={self.user_id}>"
