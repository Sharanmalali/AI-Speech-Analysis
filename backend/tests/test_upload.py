"""Upload validation & job-creation tests."""

import pytest

from tests.conftest import make_wav_bytes

pytestmark = pytest.mark.integration


def test_upload_creates_job(client, auth_headers):
    r = client.post(
        "/api/v1/audio/upload",
        headers=auth_headers,
        files={"file": ("conv.wav", make_wav_bytes(), "audio/wav")},
    )
    assert r.status_code == 202, r.text
    body = r.json()
    assert body["job_id"] and body["audio_file_id"]
    assert body["status"] == "pending"


def test_upload_requires_auth(client):
    r = client.post(
        "/api/v1/audio/upload",
        files={"file": ("conv.wav", make_wav_bytes(), "audio/wav")},
    )
    assert r.status_code == 401


def test_upload_rejects_bad_extension(client, auth_headers):
    r = client.post(
        "/api/v1/audio/upload",
        headers=auth_headers,
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert r.status_code == 400
    assert r.json()["error"]["code"] in {"unsupported_extension", "unsupported_content_type"}


def test_upload_rejects_magic_byte_mismatch(client, auth_headers):
    r = client.post(
        "/api/v1/audio/upload",
        headers=auth_headers,
        files={"file": ("fake.wav", b"NOT_A_RIFF_HEADER", "audio/wav")},
    )
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "magic_mismatch"


def test_results_conflict_before_completion(client, auth_headers):
    up = client.post(
        "/api/v1/audio/upload",
        headers=auth_headers,
        files={"file": ("conv.wav", make_wav_bytes(), "audio/wav")},
    )
    job_id = up.json()["job_id"]
    r = client.get(f"/api/v1/results/{job_id}", headers=auth_headers)
    assert r.status_code == 409


def test_delete_job(client, auth_headers):
    up = client.post(
        "/api/v1/audio/upload",
        headers=auth_headers,
        files={"file": ("conv.wav", make_wav_bytes(), "audio/wav")},
    )
    job_id = up.json()["job_id"]

    # Delete it.
    r = client.delete(f"/api/v1/jobs/{job_id}", headers=auth_headers)
    assert r.status_code == 204, r.text

    # It should no longer exist.
    assert client.get(f"/api/v1/jobs/{job_id}", headers=auth_headers).status_code == 404
    listing = client.get("/api/v1/jobs", headers=auth_headers).json()
    assert all(j["id"] != job_id for j in listing["items"])


def test_delete_job_requires_auth(client, auth_headers):
    up = client.post(
        "/api/v1/audio/upload",
        headers=auth_headers,
        files={"file": ("conv.wav", make_wav_bytes(), "audio/wav")},
    )
    job_id = up.json()["job_id"]
    assert client.delete(f"/api/v1/jobs/{job_id}").status_code == 401
