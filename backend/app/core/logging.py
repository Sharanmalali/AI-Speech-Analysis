"""Structured logging configuration.

Uses ``structlog`` on top of the standard library logging module so that
log output can be rendered either as human-readable console lines (dev) or
machine-parsable JSON (production) controlled by ``settings.LOG_JSON``.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog

from app.config import settings

_CONFIGURED = False


def configure_logging() -> None:
    """Configure standard logging + structlog. Idempotent."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    log_level = getattr(logging, settings.LOG_LEVEL, logging.INFO)

    # Route the stdlib root logger to stdout at the configured level.
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.LOG_JSON:
        renderer: Any = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=sys.stdout.isatty())

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Tame noisy third-party loggers.
    for noisy in ("uvicorn.access", "httpx", "httpcore", "urllib3", "numba"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger."""
    if not _CONFIGURED:
        configure_logging()
    return structlog.get_logger(name)  # type: ignore[return-value]
