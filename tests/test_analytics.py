import pytest

from tests.conftest import token_for


@pytest.mark.asyncio
async def test_summary(client):
    token = await token_for(client, "viewer@t.dev", "viewer12345")
    resp = await client.get(
        "/api/v1/analytics/summary", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["transaction_count"] == 4
    assert body["approval_rate"] == 0.75  # 3 settled of 4
    assert body["source"] == "postgres"


@pytest.mark.asyncio
async def test_top_merchants(client):
    token = await token_for(client, "viewer@t.dev", "viewer12345")
    resp = await client.get(
        "/api/v1/analytics/top-merchants", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["merchant_name"] == "Test Co"


@pytest.mark.asyncio
async def test_transactions_pagination(client):
    token = await token_for(client, "viewer@t.dev", "viewer12345")
    resp = await client.get(
        "/api/v1/transactions?limit=2",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 4
    assert len(body["items"]) == 2
