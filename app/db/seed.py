"""Seed the database with an admin user, merchants, and sample transactions.

Run:  python -m app.db.seed
"""
from __future__ import annotations

import asyncio
import random
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.rbac import Role
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import Merchant, Transaction, User

MERCHANTS = [
    ("Aurora Coffee", "US", "5814"),
    ("Helix Cloud", "US", "5734"),
    ("Nordic Travel", "SE", "4722"),
    ("Maple Grocers", "CA", "5411"),
    ("Lumen Energy", "GB", "4900"),
]


async def seed() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        if (await db.execute(select(User))).first():
            print("Database already seeded — skipping.")
            return

        db.add_all(
            [
                User(
                    email="admin@finstream.dev",
                    hashed_password=hash_password("admin12345"),
                    role=Role.ADMIN,
                ),
                User(
                    email="analyst@finstream.dev",
                    hashed_password=hash_password("analyst12345"),
                    role=Role.ANALYST,
                ),
                User(
                    email="viewer@finstream.dev",
                    hashed_password=hash_password("viewer12345"),
                    role=Role.VIEWER,
                ),
            ]
        )
        merchants = [Merchant(name=n, country=c, mcc=m) for n, c, m in MERCHANTS]
        db.add_all(merchants)
        await db.flush()

        statuses = ["settled"] * 8 + ["declined", "refunded"]
        now = datetime.now(UTC)
        txns = [
            Transaction(
                merchant_id=random.choice(merchants).id,
                amount=round(random.uniform(5, 950), 2),
                currency="USD",
                status=random.choice(statuses),
                card_type=random.choice(["credit", "debit", "prepaid"]),
                created_at=now - timedelta(minutes=random.randint(0, 60 * 24 * 30)),
            )
            for _ in range(500)
        ]
        db.add_all(txns)
        await db.commit()
        print("Seeded 3 users, 5 merchants, 500 transactions.")
        print("Logins -> admin@finstream.dev / admin12345  (also analyst@, viewer@)")


if __name__ == "__main__":
    asyncio.run(seed())
