"""ORM models for the financial analytics domain."""
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.rbac import Role
from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(String(20), default=Role.VIEWER, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False)  # ISO-3166 alpha-2
    mcc: Mapped[str] = mapped_column(String(4), nullable=False)      # merchant category code

    transactions: Mapped[list[Transaction]] = relationship(back_populates="merchant")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="settled", nullable=False)
    card_type: Mapped[str] = mapped_column(String(20), default="credit", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, index=True
    )

    merchant: Mapped[Merchant] = relationship(back_populates="transactions")

    # Composite index supporting the hot analytical access path
    # (filter by time window, group by merchant) — see sql/postgres/analytics_queries.sql
    __table_args__ = (
        Index("ix_txn_created_merchant", "created_at", "merchant_id"),
        Index("ix_txn_status", "status"),
    )
