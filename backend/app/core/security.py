"""Security primitives: password hashing and JWT token management.

Supports two token types: short-lived ``access`` tokens (sent as Bearer in
the Authorization header) and longer-lived ``refresh`` tokens (delivered via
an HttpOnly cookie). Tokens are signed with HS256 using ``JWT_SECRET_KEY``.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import jwt

from app.config import settings
from app.core.exceptions import AuthenticationError

TokenType = Literal["access", "refresh"]

# bcrypt has a hard 72-byte limit on the input password.
_BCRYPT_MAX_BYTES = 72


# --------------------------------------------------------------------------- #
# Password hashing (using the maintained ``bcrypt`` library directly)
# --------------------------------------------------------------------------- #
def _normalize(password: str) -> bytes:
    """Encode and truncate the password to bcrypt's 72-byte limit."""
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(plain_password: str) -> str:
    """Return a bcrypt hash of the given password."""
    import bcrypt

    return bcrypt.hashpw(_normalize(plain_password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its bcrypt hash."""
    import bcrypt

    try:
        return bcrypt.checkpw(_normalize(plain_password), hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# --------------------------------------------------------------------------- #
# JWT helpers
# --------------------------------------------------------------------------- #
def _create_token(
    subject: str,
    token_type: TokenType,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "jti": uuid.uuid4().hex,
        "iss": settings.APP_NAME,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(
    subject: str, *, role: str | None = None, extra_claims: dict[str, Any] | None = None
) -> str:
    """Create a short-lived access token."""
    claims = dict(extra_claims or {})
    if role is not None:
        claims["role"] = role
    return _create_token(
        subject,
        "access",
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        claims,
    )


def create_refresh_token(subject: str) -> str:
    """Create a longer-lived refresh token."""
    return _create_token(
        subject,
        "refresh",
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str, *, expected_type: TokenType | None = None) -> dict[str, Any]:
    """Decode and validate a JWT, raising :class:`AuthenticationError` on failure."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["exp", "sub", "type"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationError("Token has expired.", code="token_expired") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthenticationError("Invalid authentication token.") from exc

    if expected_type is not None and payload.get("type") != expected_type:
        raise AuthenticationError(
            f"Expected a {expected_type} token.", code="invalid_token_type"
        )
    return payload


def decode_supabase_token(token: str) -> dict[str, Any]:
    """Validate a Supabase-issued JWT using the Supabase JWT secret.

    Supabase signs auth tokens with the project's JWT secret (HS256) and an
    ``authenticated`` audience. Returns the decoded claims.
    """
    if not settings.SUPABASE_JWT_SECRET:
        raise AuthenticationError(
            "Supabase auth is not configured.", code="supabase_not_configured"
        )
    try:
        return jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
            options={"verify_exp": True},
        )
    except jwt.InvalidTokenError as exc:
        raise AuthenticationError("Invalid Supabase token.") from exc
