"""Database engine, session factory and FastAPI session dependency."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _build_engine() -> Engine:
    """Create the SQLAlchemy engine with environment-aware pooling."""
    url = settings.database_url_sync
    connect_args: dict[str, object] = {}
    engine_kwargs: dict[str, object] = {
        "echo": settings.DB_ECHO,
        "pool_pre_ping": True,
        "future": True,
    }

    if url.startswith("sqlite"):
        # Local dev fallback — SQLite needs this flag for multithreaded access.
        connect_args["check_same_thread"] = False
    else:
        engine_kwargs.update(
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_recycle=1800,
        )

    logger.info("database_engine_init", dialect=url.split("://", 1)[0])
    return create_engine(url, connect_args=connect_args, **engine_kwargs)


engine: Engine = _build_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a transactional database session."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Context manager for use outside the request lifecycle (Celery, scripts)."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
