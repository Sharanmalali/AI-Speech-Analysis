"""Database initialisation helpers (dev/test convenience).

In production, schema changes are managed exclusively through Alembic
migrations. ``create_all`` is provided only for local development and the
test suite where a throwaway SQLite/Postgres schema is acceptable.
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.database.base import Base
from app.database.session import engine

# Importing the models package registers all tables on Base.metadata.
import app.models  # noqa: F401

logger = get_logger(__name__)


def create_all() -> None:
    """Create all tables defined on the metadata."""
    logger.info("db_create_all_start")
    Base.metadata.create_all(bind=engine)
    logger.info("db_create_all_done", tables=list(Base.metadata.tables.keys()))


def drop_all() -> None:
    """Drop all tables — destructive, intended for tests only."""
    Base.metadata.drop_all(bind=engine)
