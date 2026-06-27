"""Admin-only endpoints: user management and audit-trail access."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.database import get_db
from app.dependencies import require_admin
from app.models import AuditLog, User
from app.models.enums import AuditAction
from app.schemas.admin import AuditLogRead
from app.schemas.common import MessageResponse, Page
from app.schemas.user import UserRead, UserRoleUpdate
from app.services import auth_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=Page[UserRead], summary="List users")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> Page[UserRead]:
    offset = (page - 1) * page_size
    total = db.execute(select(func.count()).select_from(User)).scalar_one()
    rows = (
        db.execute(select(User).order_by(User.created_at.desc()).offset(offset).limit(page_size))
        .scalars()
        .all()
    )
    return Page[UserRead](
        items=[UserRead.model_validate(u) for u in rows],
        total=int(total),
        page=page,
        page_size=page_size,
    )


@router.patch("/users/{user_id}/role", response_model=UserRead, summary="Change a user's role")
async def change_role(
    user_id: uuid.UUID,
    payload: UserRoleUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> UserRead:
    target = db.get(User, user_id)
    if target is None:
        raise NotFoundError("User not found.")
    previous = target.role
    target.role = payload.role
    db.add(target)
    db.flush()
    auth_service.record_audit(
        db,
        action=AuditAction.ROLE_CHANGED,
        user_id=admin.id,
        resource_type="user",
        resource_id=str(target.id),
        detail={"from": previous.value, "to": payload.role.value},
    )
    return UserRead.model_validate(target)


@router.patch("/users/{user_id}/deactivate", response_model=MessageResponse,
              summary="Deactivate a user account")
async def deactivate_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> MessageResponse:
    target = db.get(User, user_id)
    if target is None:
        raise NotFoundError("User not found.")
    target.is_active = False
    db.add(target)
    db.flush()
    return MessageResponse(message="User deactivated.")


@router.get("/audit-logs", response_model=Page[AuditLogRead], summary="List audit-trail entries")
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> Page[AuditLogRead]:
    offset = (page - 1) * page_size
    total = db.execute(select(func.count()).select_from(AuditLog)).scalar_one()
    rows = (
        db.execute(
            select(AuditLog).order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size)
        )
        .scalars()
        .all()
    )
    return Page[AuditLogRead](
        items=[AuditLogRead.model_validate(a) for a in rows],
        total=int(total),
        page=page,
        page_size=page_size,
    )
