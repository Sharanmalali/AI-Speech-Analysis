"""Authentication request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserProfile


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenPair(BaseModel):
    """Issued on successful authentication."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # access token lifetime in seconds


class AccessToken(BaseModel):
    """Returned by the refresh endpoint."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthResponse(BaseModel):
    """Full auth payload returned on login/register."""

    user: UserProfile
    tokens: TokenPair


class SupabaseTokenExchange(BaseModel):
    """Exchange a Supabase access token (from social/email login on the
    frontend) for an AblePro session, provisioning the local user if needed.
    """

    supabase_access_token: str = Field(min_length=10)


class RefreshRequest(BaseModel):
    """Optional explicit refresh token (otherwise read from cookie)."""

    refresh_token: str | None = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class TokenPayload(BaseModel):
    """Decoded JWT claims of interest."""

    sub: str
    type: str
    role: str | None = None
    exp: int | None = None
