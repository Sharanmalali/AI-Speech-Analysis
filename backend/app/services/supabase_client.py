"""Lazy Supabase client factory.

The Supabase Python client is created on first use with the service-role key
(server-side privileged operations: storage, auth admin). Returns ``None`` if
Supabase is not configured so callers can fall back to local behaviour.
"""

from __future__ import annotations

import threading
from typing import Any

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_client: Any = None
_lock = threading.Lock()


def get_supabase() -> Any | None:
    """Return a cached Supabase client, or ``None`` when not configured."""
    global _client
    if _client is not None:
        return _client
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        return None
    with _lock:
        if _client is None:
            try:
                from supabase import create_client

                _client = create_client(
                    settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY
                )
                logger.info("supabase_client_ready")
            except Exception as exc:  # noqa: BLE001
                logger.error("supabase_client_init_failed", error=str(exc))
                return None
    return _client
