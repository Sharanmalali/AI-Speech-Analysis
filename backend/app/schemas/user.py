"""User-related Pydantic schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import UserRole
from app.schemas.common import TimestampedSchema


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = Field(default=None, max_length=200)


class UserCreate(UserBase):
    """Payload for local registration."""

    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=200)
    is_active: bool | None = None


class UserRoleUpdate(BaseModel):
    """Admin-only role change payload."""

    role: UserRole


class UserRead(TimestampedSchema):
    id: uuid.UUID
    email: EmailStr
    full_name: str | None
    role: UserRole
    is_active: bool
    is_verified: bool


class UserProfile(BaseModel):
    """Lightweight current-user representation embedded in auth responses."""

    id: uuid.UUID
    email: EmailStr
    full_name: str | None
    role: UserRole
    is_active: bool
    is_verified: bool

    model_config = {"from_attributes": True}
