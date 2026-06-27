"""Authentication endpoints: register, login, refresh, logout, profile.

Access tokens are returned in the JSON body (Bearer). Refresh tokens are
additionally set as an HttpOnly, SameSite cookie so browser clients never
expose them to JavaScript.

Note: this module deliberately does NOT use ``from __future__ import
annotations``. The SlowAPI ``@limiter.limit`` decorator wraps the endpoint
functions; with stringized annotations FastAPI would resolve request-body
models against SlowAPI's module globals and misclassify them as query
params. Keeping real annotation objects avoids that.
"""

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.exceptions import AuthenticationError
from app.core.rate_limit import limiter
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_supabase_token,
    decode_token,
)
from app.database import get_db
from app.dependencies import client_ip, get_current_user
from app.models import User
from app.models.enums import AuditAction
from app.schemas.auth import (
    AccessToken,
    AuthResponse,
    LoginRequest,
    SupabaseTokenExchange,
    TokenPair,
)
from app.schemas.common import MessageResponse
from app.schemas.user import UserCreate, UserProfile
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["authentication"])

REFRESH_COOKIE = "ablepro_refresh"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=token,
        httponly=True,
        secure=settings.SECURE_COOKIES,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        path="/",
    )


def _issue_tokens(user: User) -> TokenPair:
    access = create_access_token(str(user.id), role=user.role.value)
    refresh = create_refresh_token(str(user.id))
    return TokenPair(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new local account",
)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def register(
    request: Request,
    response: Response,
    payload: UserCreate,
    db: Session = Depends(get_db),
) -> AuthResponse:
    user = auth_service.register_user(
        db,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
    )
    auth_service.record_audit(
        db,
        action=AuditAction.REGISTER,
        user_id=user.id,
        ip_address=client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    tokens = _issue_tokens(user)
    _set_refresh_cookie(response, tokens.refresh_token)
    return AuthResponse(user=UserProfile.model_validate(user), tokens=tokens)


@router.post("/login", response_model=AuthResponse, summary="Login with email & password")
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def login(
    request: Request,
    response: Response,
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> AuthResponse:
    try:
        user = auth_service.authenticate_user(
            db, email=payload.email, password=payload.password
        )
    except AuthenticationError:
        auth_service.record_audit(
            db,
            action=AuditAction.LOGIN_FAILED,
            ip_address=client_ip(request),
            user_agent=request.headers.get("user-agent"),
            detail={"email": payload.email},
        )
        raise

    auth_service.record_audit(
        db,
        action=AuditAction.LOGIN,
        user_id=user.id,
        ip_address=client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    tokens = _issue_tokens(user)
    _set_refresh_cookie(response, tokens.refresh_token)
    return AuthResponse(user=UserProfile.model_validate(user), tokens=tokens)


@router.post(
    "/supabase",
    response_model=AuthResponse,
    summary="Exchange a Supabase token (email/Google login) for an AblePro session",
)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def supabase_exchange(
    request: Request,
    response: Response,
    payload: SupabaseTokenExchange,
    db: Session = Depends(get_db),
) -> AuthResponse:
    claims = decode_supabase_token(payload.supabase_access_token)
    user = auth_service.provision_from_supabase(db, claims)
    auth_service.record_audit(
        db,
        action=AuditAction.LOGIN,
        user_id=user.id,
        ip_address=client_ip(request),
        user_agent=request.headers.get("user-agent"),
        detail={"provider": "supabase"},
    )
    tokens = _issue_tokens(user)
    _set_refresh_cookie(response, tokens.refresh_token)
    return AuthResponse(user=UserProfile.model_validate(user), tokens=tokens)


@router.post("/refresh", response_model=AccessToken, summary="Refresh the access token")
async def refresh(
    request: Request,
    db: Session = Depends(get_db),
) -> AccessToken:
    token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        # Allow refresh token in the Authorization header as a fallback.
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:]
    if not token:
        raise AuthenticationError("Missing refresh token.")

    payload = decode_token(token, expected_type="refresh")
    user = auth_service.get_user_by_id(db, payload.get("sub", ""))
    if user is None or not user.is_active:
        raise AuthenticationError("Invalid refresh token.")

    access = create_access_token(str(user.id), role=user.role.value)
    return AccessToken(access_token=access, expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)


@router.post("/logout", response_model=MessageResponse, summary="Logout (clear refresh cookie)")
async def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MessageResponse:
    response.delete_cookie(REFRESH_COOKIE, path="/", domain=settings.COOKIE_DOMAIN)
    auth_service.record_audit(
        db,
        action=AuditAction.LOGOUT,
        user_id=user.id,
        ip_address=client_ip(request),
    )
    return MessageResponse(message="Logged out successfully.")


@router.get("/me", response_model=UserProfile, summary="Get the current user profile")
async def me(user: User = Depends(get_current_user)) -> UserProfile:
    return UserProfile.model_validate(user)
