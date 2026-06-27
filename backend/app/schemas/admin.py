"""Admin schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from app.models.enums import AuditAction
from app.schemas.common import ORMModel


class AuditLogRead(ORMModel):
    id: uuid.UUID
    user_id: uuid.UUID | None
    action: AuditAction
    resource_type: str | None
    resource_id: str | None
    ip_address: str | None
    detail: dict | None
    created_at: datetime
