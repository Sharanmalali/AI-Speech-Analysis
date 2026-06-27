"""Report schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel

from app.schemas.common import TimestampedSchema


class ReportRead(TimestampedSchema):
    id: uuid.UUID
    job_id: uuid.UUID
    filename: str
    size_bytes: int | None
    page_count: int | None


class ReportDownloadResponse(BaseModel):
    download_url: str
    filename: str
    expires_in: int
