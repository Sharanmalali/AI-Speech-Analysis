"""Object storage abstraction.

Two interchangeable backends implement the same interface:

* :class:`SupabaseStorage` — production, backed by Supabase Storage buckets.
* :class:`LocalStorage`    — development/tests, backed by the local filesystem.

The active backend is selected automatically based on configuration.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Protocol

from app.config import settings
from app.core.exceptions import StorageError
from app.core.logging import get_logger
from app.services.supabase_client import get_supabase

logger = get_logger(__name__)


class StorageBackend(Protocol):
    """Common storage interface."""

    def upload(self, path: str, data: bytes, content_type: str) -> str: ...
    def download(self, path: str) -> bytes: ...
    def signed_url(self, path: str, expires_in: int = 3600) -> str: ...
    def delete(self, path: str) -> None: ...


class LocalStorage:
    """Filesystem-backed storage for development and tests."""

    def __init__(self, root: Path | None = None) -> None:
        self._root = root or (settings.UPLOAD_TMP_DIR.parent / "objects")
        self._root.mkdir(parents=True, exist_ok=True)

    def _full(self, path: str) -> Path:
        target = (self._root / path).resolve()
        # Prevent path traversal outside the storage root.
        if not str(target).startswith(str(self._root.resolve())):
            raise StorageError("Invalid storage path.", code="path_traversal")
        return target

    def upload(self, path: str, data: bytes, content_type: str) -> str:
        full = self._full(path)
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_bytes(data)
        logger.info("local_storage_upload", path=path, bytes=len(data))
        return path

    def download(self, path: str) -> bytes:
        full = self._full(path)
        if not full.exists():
            raise StorageError(f"Object not found: {path}", code="object_missing")
        return full.read_bytes()

    def signed_url(self, path: str, expires_in: int = 3600) -> str:
        # Local backend exposes a relative API path; the results router serves it.
        return f"/local-storage/{path}"

    def delete(self, path: str) -> None:
        full = self._full(path)
        if full.exists():
            full.unlink()

    def local_path(self, path: str) -> Path:
        """Return the on-disk path (used by the pipeline to read the file)."""
        return self._full(path)


class SupabaseStorage:
    """Supabase Storage-backed implementation."""

    def __init__(self, bucket: str | None = None) -> None:
        self._bucket = bucket or settings.SUPABASE_STORAGE_BUCKET

    def _storage(self):  # type: ignore[no-untyped-def]
        client = get_supabase()
        if client is None:
            raise StorageError("Supabase is not configured.", code="supabase_unconfigured")
        return client.storage.from_(self._bucket)

    def upload(self, path: str, data: bytes, content_type: str) -> str:
        try:
            self._storage().upload(
                path=path,
                file=data,
                file_options={"content-type": content_type, "upsert": "true"},
            )
            logger.info("supabase_storage_upload", path=path, bytes=len(data))
            return path
        except Exception as exc:  # noqa: BLE001
            raise StorageError(f"Upload failed: {exc}") from exc

    def download(self, path: str) -> bytes:
        try:
            return self._storage().download(path)
        except Exception as exc:  # noqa: BLE001
            raise StorageError(f"Download failed: {exc}") from exc

    def signed_url(self, path: str, expires_in: int = 3600) -> str:
        try:
            res = self._storage().create_signed_url(path, expires_in)
            return res.get("signedURL") or res.get("signed_url") or ""
        except Exception as exc:  # noqa: BLE001
            raise StorageError(f"Signed URL failed: {exc}") from exc

    def delete(self, path: str) -> None:
        try:
            self._storage().remove([path])
        except Exception as exc:  # noqa: BLE001
            raise StorageError(f"Delete failed: {exc}") from exc


_backend: StorageBackend | None = None


def get_storage() -> StorageBackend:
    """Return the configured storage backend (Supabase if available, else local)."""
    global _backend
    if _backend is None:
        if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
            _backend = SupabaseStorage()
            logger.info("storage_backend", backend="supabase")
        else:
            _backend = LocalStorage()
            logger.info("storage_backend", backend="local")
    return _backend
