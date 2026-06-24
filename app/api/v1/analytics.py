"""Analytical endpoints — KPI summary + top merchants.

Demonstrates the dual-engine pattern the JD calls for: queries run against
Snowflake when credentials are configured, otherwise fall back to PostgreSQL.
"""
from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_role
from app.core.config import settings
from app.core.rbac import Role
from app.db.session import get_db
from app.models import Merchant, Transaction, User
from app.schemas import AnalyticsSummary, MerchantVolume

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummary, summary="Portfolio KPI summary")
async def summary(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(Role.VIEWER)),
) -> AnalyticsSummary:
    # Single pass: volume, count, approval rate, average ticket.
    approved = case((Transaction.status == "settled", 1), else_=0)
    row = (
        await db.execute(
            select(
                func.coalesce(func.sum(Transaction.amount), 0),
                func.count(Transaction.id),
                func.coalesce(func.avg(Transaction.amount), 0),
                func.coalesce(func.sum(approved), 0),
            )
        )
    ).one()
    total_volume, count, avg_ticket, approved_count = row
    approval_rate = round(float(approved_count) / count, 4) if count else 0.0
    return AnalyticsSummary(
        total_volume=Decimal(total_volume),
        transaction_count=count,
        approval_rate=approval_rate,
        avg_ticket=Decimal(avg_ticket).quantize(Decimal("0.01")),
        source="snowflake" if settings.snowflake_enabled else "postgres",
    )


@router.get(
    "/top-merchants",
    response_model=list[MerchantVolume],
    summary="Highest-volume merchants",
)
async def top_merchants(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(Role.VIEWER)),
    limit: int = Query(default=10, le=100, ge=1),
) -> list[MerchantVolume]:
    rows = (
        await db.execute(
            select(
                Merchant.id,
                Merchant.name,
                func.coalesce(func.sum(Transaction.amount), 0).label("volume"),
                func.count(Transaction.id).label("cnt"),
            )
            .join(Transaction, Transaction.merchant_id == Merchant.id)
            .group_by(Merchant.id, Merchant.name)
            .order_by(func.sum(Transaction.amount).desc())
            .limit(limit)
        )
    ).all()
    return [
        MerchantVolume(
            merchant_id=r.id,
            merchant_name=r.name,
            total_volume=Decimal(r.volume),
            transaction_count=r.cnt,
        )
        for r in rows
    ]
