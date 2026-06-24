"""Transaction ingestion + paginated retrieval."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_role
from app.core.rbac import Role
from app.db.session import get_db
from app.models import Merchant, Transaction, User
from app.schemas import Page, TransactionCreate, TransactionOut

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=Page, summary="List transactions (paginated, filterable)")
async def list_transactions(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(Role.VIEWER)),
    merchant_id: int | None = Query(default=None, gt=0),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, le=200, ge=1),
    offset: int = Query(default=0, ge=0),
) -> Page:
    conditions = []
    if merchant_id is not None:
        conditions.append(Transaction.merchant_id == merchant_id)
    if status_filter is not None:
        conditions.append(Transaction.status == status_filter)

    base = select(Transaction)
    if conditions:
        base = base.where(*conditions)

    total = await db.scalar(select(func.count()).select_from(base.subquery()))
    rows = (
        await db.execute(
            base.order_by(Transaction.created_at.desc()).limit(limit).offset(offset)
        )
    ).scalars().all()
    return Page(total=total or 0, limit=limit, offset=offset, items=list(rows))


@router.post(
    "",
    response_model=TransactionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a transaction (analyst+)",
)
async def create_transaction(
    payload: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(Role.ANALYST)),
) -> Transaction:
    merchant = await db.get(Merchant, payload.merchant_id)
    if merchant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found")
    txn = Transaction(**payload.model_dump())
    db.add(txn)
    await db.commit()
    await db.refresh(txn)
    return txn
