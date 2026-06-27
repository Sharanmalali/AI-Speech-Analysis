"""Authentication & user-provisioning business logic.

Pure functions operating on a SQLAlchemy session — no FastAPI imports — so
they are easy to unit test and reuse from Celery tasks or scripts.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, ConflictError
from app.core.logging import get_logger
from app.core.security import hash_password, verify_password
from app.models import AuditLog, User
from app.models.enums import AuditAction, UserRole

logger = get_logger(__name__)


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.execute(select(User).where(User.email == email.lower())).scalar_one_or_none()


def get_user_by_id(db: Session, user_id: uuid.UUID | str) -> User | None:
    if isinstance(user_id, str):
        try:
            user_id = uuid.UUID(user_id)
        except ValueError:
            return None
    return db.get(User, user_id)


def get_user_by_supabase_uid(db: Session, supabase_uid: str) -> User | None:
    return db.execute(
        select(User).where(User.supabase_uid == supabase_uid)
    ).scalar_one_or_none()


def register_user(
    db: Session,
    *,
    email: str,
    password: str,
    full_name: str | None = None,
    role: UserRole = UserRole.USER,
) -> User:
    """Create a local email/password user."""
    email = email.lower()
    if get_user_by_email(db, email) is not None:
        raise ConflictError("An account with this email already exists.")

    user = User(
        email=email,
        full_name=full_name,
        hashed_password=hash_password(password),
        role=role,
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.flush()
    logger.info("user_registered", user_id=str(user.id), email=email)
    return user


def authenticate_user(db: Session, *, email: str, password: str) -> User:
    """Validate credentials and return the user, or raise AuthenticationError."""
    user = get_user_by_email(db, email)
    if user is None or not user.hashed_password:
        raise AuthenticationError("Invalid email or password.")
    if not verify_password(password, user.hashed_password):
        raise AuthenticationError("Invalid email or password.")
    if not user.is_active:
        raise AuthenticationError("This account is disabled.", code="account_disabled")
    return user


def provision_from_supabase(db: Session, claims: dict[str, Any]) -> User:
    """Find or create a local user from validated Supabase JWT claims.

    Supabase claims include ``sub`` (the user uid), ``email`` and an optional
    ``user_metadata`` dict (name, full_name, etc.).
    """
    supabase_uid = str(claims.get("sub"))
    email = (claims.get("email") or "").lower()
    metadata = claims.get("user_metadata") or {}
    full_name = metadata.get("full_name") or metadata.get("name")

    user = get_user_by_supabase_uid(db, supabase_uid)
    if user is not None:
        return user

    # Link to an existing email account if one exists, else create a new one.
    user = get_user_by_email(db, email) if email else None
    if user is not None:
        user.supabase_uid = supabase_uid
        user.is_verified = True
        db.flush()
        return user

    user = User(
        email=email or f"{supabase_uid}@supabase.local",
        full_name=full_name,
        supabase_uid=supabase_uid,
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.flush()
    logger.info("user_provisioned_from_supabase", user_id=str(user.id), email=user.email)
    return user


def record_audit(
    db: Session,
    *,
    action: AuditAction,
    user_id: uuid.UUID | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    detail: dict[str, Any] | None = None,
) -> AuditLog:
    """Append an immutable audit-trail entry."""
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        detail=detail,
    )
    db.add(entry)
    db.flush()
    return entry
