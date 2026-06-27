"""Rate limiting via SlowAPI backed by Redis.

The limiter keys requests by authenticated user id when available, falling
back to the client's remote address for anonymous traffic. This lets us
apply distinct quotas to authenticated and anonymous callers.
"""

from __future__ import annotations

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings


def _rate_limit_key(request: Request) -> str:
    """Identify the caller for rate-limiting purposes."""
    user = getattr(request.state, "user", None)
    if user is not None:
        user_id = getattr(user, "id", None)
        if user_id is not None:
            return f"user:{user_id}"
    return f"ip:{get_remote_address(request)}"


# Using Redis as the shared store enables consistent limits across workers.
limiter = Limiter(
    key_func=_rate_limit_key,
    storage_uri=str(settings.REDIS_URL),
    default_limits=[settings.RATE_LIMIT_DEFAULT] if settings.RATE_LIMIT_ENABLED else [],
    enabled=settings.RATE_LIMIT_ENABLED,
    headers_enabled=True,
)
