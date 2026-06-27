"""Health and readiness probes used by load balancers and orchestrators."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from sqlalchemy import text

from app.config import settings
from app.core.logging import get_logger
from app.database import engine

logger = get_logger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness probe")
async def health() -> dict[str, Any]:
    """Lightweight liveness check — returns 200 if the process is up."""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@router.get("/ready", summary="Readiness probe")
async def ready() -> dict[str, Any]:
    """Readiness check — verifies critical dependencies are reachable."""
    checks: dict[str, str] = {}

    # Database connectivity
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:  # noqa: BLE001
        logger.warning("readiness_db_failed", error=str(exc))
        checks["database"] = "unavailable"

    overall = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": overall, "checks": checks}
