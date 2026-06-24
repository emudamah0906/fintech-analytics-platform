import pytest

from tests.conftest import token_for


@pytest.mark.asyncio
async def test_viewer_cannot_create_transaction(client):
    token = await token_for(client, "viewer@t.dev", "viewer12345")
    resp = await client.post(
        "/api/v1/transactions",
        headers={"Authorization": f"Bearer {token}"},
        json={"merchant_id": 1, "amount": 12.50},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_analyst_can_create_transaction(client):
    token = await token_for(client, "analyst@t.dev", "analyst12345")
    resp = await client.post(
        "/api/v1/transactions",
        headers={"Authorization": f"Bearer {token}"},
        json={"merchant_id": 1, "amount": 12.50},
    )
    assert resp.status_code == 201
    assert resp.json()["merchant_id"] == 1


@pytest.mark.asyncio
async def test_viewer_cannot_create_user(client):
    token = await token_for(client, "viewer@t.dev", "viewer12345")
    resp = await client.post(
        "/api/v1/auth/users",
        headers={"Authorization": f"Bearer {token}"},
        json={"email": "x@t.dev", "password": "password123", "role": "viewer"},
    )
    assert resp.status_code == 403
