"""Shared pytest fixtures.

Uses an isolated on-disk SQLite database and a local filesystem storage
backend so tests run without Postgres, Redis, Supabase or the heavy ML stack.
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

# Configure the environment BEFORE importing the app/settings.
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-please-change-0123456789abcdef")
# Force the SQLite + local-storage test fallbacks regardless of any values in a
# developer's real .env (env vars take precedence over the dotenv file, and the
# empty-string validator coerces these to None).
os.environ["DATABASE_URL"] = ""
os.environ["SUPABASE_URL"] = ""
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = ""
os.environ["GEMINI_API_KEY"] = ""

import app.routers.upload as upload_mod  # noqa: E402
from app.database.init_db import create_all, drop_all  # noqa: E402
from app.database.session import SessionLocal  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _isolated_storage() -> Generator[None, None, None]:
    """Point local storage at a temp dir for the whole test session."""
    tmp = Path(tempfile.mkdtemp(prefix="ablepro-test-"))
    os.environ["UPLOAD_TMP_DIR"] = str(tmp / "tmp")
    yield


@pytest.fixture()
def db_session():
    """Create all tables, yield a session, then drop everything."""
    create_all()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        drop_all()


@pytest.fixture()
def client(db_session, monkeypatch):
    """A TestClient with the DB initialised, Celery dispatch stubbed and
    storage forced to the local filesystem backend (hermetic — ignores any
    Supabase placeholders that may exist in a developer's .env)."""
    import tempfile
    from pathlib import Path

    from fastapi.testclient import TestClient

    import app.services.storage as storage_mod

    # Never touch a real broker in tests.
    monkeypatch.setattr(upload_mod, "enqueue_audio_job", lambda job_id: "test-task-id")

    # Force local filesystem storage into a throwaway directory.
    root = Path(tempfile.mkdtemp(prefix="ablepro-store-")) / "objects"
    monkeypatch.setattr(storage_mod, "_backend", storage_mod.LocalStorage(root=root))

    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth_headers(client) -> dict[str, str]:
    """Register a user and return Authorization headers."""
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "tester@ablepro.ai", "password": "Sup3rSecret!", "full_name": "Tester"},
    )
    assert resp.status_code == 201, resp.text
    token = resp.json()["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def make_wav_bytes() -> bytes:
    """Return a minimal but RIFF-valid WAV byte payload for upload tests."""
    return b"RIFF" + b"\x24\x00\x00\x00" + b"WAVE" + b"fmt " + b"\x00" * 256
