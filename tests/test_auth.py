import pytest

from tests.conftest import token_for


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_login_success_and_me(client):
    token = await token_for(client, "admin@t.dev", "admin12345")
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "admin@t.dev"
    assert resp.json()["role"] == "admin"


@pytest.mark.asyncio
async def test_login_bad_password(client):
    resp = await client.post(
        "/api/v1/auth/token", data={"username": "admin@t.dev", "password": "wrong"}
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_requires_token(client):
    resp = await client.get("/api/v1/analytics/summary")
    assert resp.status_code == 401
