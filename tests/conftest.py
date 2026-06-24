"""Pytest fixtures: in-memory SQLite app + seeded data + auth helpers."""
from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.rbac import Role
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Merchant, Transaction, User

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    engine = create_async_engine(TEST_DB_URL)
    sessionmaker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with sessionmaker() as db:
        db.add_all(
            [
                User(
                    email="admin@t.dev",
                    hashed_password=hash_password("admin12345"),
                    role=Role.ADMIN,
                ),
                User(
                    email="analyst@t.dev",
                    hashed_password=hash_password("analyst12345"),
                    role=Role.ANALYST,
                ),
                User(
                    email="viewer@t.dev",
                    hashed_password=hash_password("viewer12345"),
                    role=Role.VIEWER,
                ),
            ]
        )
        m = Merchant(name="Test Co", country="US", mcc="5999")
        db.add(m)
        await db.flush()
        db.add_all([Transaction(merchant_id=m.id, amount=100, status="settled") for _ in range(3)])
        db.add(Transaction(merchant_id=m.id, amount=50, status="declined"))
        await db.commit()

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with sessionmaker() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    # Skip lifespan (table creation/logging) — handled above.
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
    await engine.dispose()


async def token_for(client: AsyncClient, email: str, password: str) -> str:
    resp = await client.post(
        "/api/v1/auth/token", data={"username": email, "password": password}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]
