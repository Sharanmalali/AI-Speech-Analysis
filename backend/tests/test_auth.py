"""Authentication & authorization tests."""

import pytest

pytestmark = pytest.mark.integration


def test_register_and_me(client):
    r = client.post(
        "/api/v1/auth/register",
        json={"email": "a@ablepro.ai", "password": "Sup3rSecret!", "full_name": "A"},
    )
    assert r.status_code == 201
    token = r.json()["tokens"]["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "a@ablepro.ai"
    assert me.json()["role"] == "user"


def test_duplicate_registration_conflicts(client):
    payload = {"email": "dup@ablepro.ai", "password": "Sup3rSecret!"}
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    assert client.post("/api/v1/auth/register", json=payload).status_code == 409


def test_login_wrong_password(client):
    client.post("/api/v1/auth/register", json={"email": "b@ablepro.ai", "password": "Sup3rSecret!"})
    r = client.post("/api/v1/auth/login", json={"email": "b@ablepro.ai", "password": "nope"})
    assert r.status_code == 401


def test_me_requires_auth(client):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_refresh_and_logout_flow(client):
    client.post("/api/v1/auth/register", json={"email": "c@ablepro.ai", "password": "Sup3rSecret!"})
    login = client.post("/api/v1/auth/login", json={"email": "c@ablepro.ai", "password": "Sup3rSecret!"})
    assert login.status_code == 200
    assert client.cookies.get("ablepro_refresh")

    refreshed = client.post("/api/v1/auth/refresh")
    assert refreshed.status_code == 200
    token = refreshed.json()["access_token"]

    out = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert out.status_code == 200


def test_admin_route_forbidden_for_user(client, auth_headers):
    r = client.get("/api/v1/admin/users", headers=auth_headers)
    assert r.status_code == 403
