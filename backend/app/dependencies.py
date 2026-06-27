"""Reusable FastAPI dependencies: authentication, RBAC and request context."""

from __future__ import annotations

from collections.abc import Callable, Iterable

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import decode_token
from app.database import get_db
from app.models import User
from app.models.enums import UserRole
from app.services import auth_service

# auto_error=False lets us emit our structured AuthenticationError instead of
# Starlette's default 403 for missing credentials.
_bearer_scheme = HTTPBearer(auto_error=False, description="JWT access token")


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve and return the authenticated user from a Bearer access token."""
    if credentials is None or not credentials.credentials:
        raise AuthenticationError("Missing authentication credentials.")

    payload = decode_token(credentials.credentials, expected_type="access")
    subject = payload.get("sub")
    if not subject:
        raise AuthenticationError("Malformed token: missing subject.")

    user = auth_service.get_user_by_id(db, subject)
    if user is None:
        raise AuthenticationError("User no longer exists.")
    if not user.is_active:
        raise AuthenticationError("This account is disabled.", code="account_disabled")

    # Expose the user on request.state for rate-limiting and audit middleware.
    request.state.user = user
    return user


def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    """Alias dependency emphasising the active-user contract."""
    return user


def get_optional_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """Return the user if a valid token is present, else ``None`` (anonymous)."""
    if credentials is None or not credentials.credentials:
        return None
    try:
        return get_current_user(request, credentials, db)
    except AuthenticationError:
        return None


def require_roles(*roles: UserRole) -> Callable[[User], User]:
    """Dependency factory enforcing that the user holds one of ``roles``."""
    allowed: Iterable[UserRole] = roles

    def _dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed and user.role != UserRole.ADMIN:
            raise AuthorizationError(
                "Insufficient privileges for this operation.",
                details={"required_roles": [r.value for r in roles]},
            )
        return user

    return _dependency


# Convenience pre-bound role dependencies.
require_admin = require_roles(UserRole.ADMIN)
require_doctor = require_roles(UserRole.DOCTOR)


def client_ip(request: Request) -> str | None:
    """Best-effort client IP, honouring the X-Forwarded-For header."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None
