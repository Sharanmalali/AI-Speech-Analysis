"""Unit tests for utility helpers."""

import pytest

from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.utils.files import get_extension, sniff_magic_bytes
from app.utils.timestamp import format_range, format_timestamp

pytestmark = pytest.mark.unit


def test_format_timestamp():
    assert format_timestamp(0) == "00:00"
    assert format_timestamp(65) == "01:05"
    assert format_timestamp(3661) == "01:01:01"


def test_format_range():
    assert format_range(5, 8) == "[00:05 - 00:08]"


def test_password_roundtrip():
    h = hash_password("Sup3rSecret!")
    assert verify_password("Sup3rSecret!", h)
    assert not verify_password("wrong", h)


def test_long_password_truncated_not_error():
    # bcrypt 72-byte limit must be handled gracefully.
    pwd = "x" * 200
    h = hash_password(pwd)
    assert verify_password(pwd, h)


def test_jwt_roundtrip():
    token = create_access_token("user-123", role="doctor")
    payload = decode_token(token, expected_type="access")
    assert payload["sub"] == "user-123"
    assert payload["role"] == "doctor"


def test_get_extension():
    assert get_extension("a/b/c.WAV") == "wav"
    assert get_extension("noext") == ""


def test_magic_bytes_wav_ok():
    sniff_magic_bytes(b"RIFFxxxxWAVE", "wav")  # should not raise


def test_magic_bytes_mismatch_raises():
    from app.core.exceptions import FileValidationError

    with pytest.raises(FileValidationError):
        sniff_magic_bytes(b"XXXX", "wav")
