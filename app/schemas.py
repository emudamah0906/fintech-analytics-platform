"""Pydantic v2 request/response contracts (the API's typed surface)."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.rbac import Role


# ---- Auth ----
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Role = Role.VIEWER


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    role: Role


# ---- Merchants ----
class MerchantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    country: str
    mcc: str


# ---- Transactions ----
class TransactionCreate(BaseModel):
    merchant_id: int = Field(gt=0)
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    status: str = Field(default="settled", pattern="^(settled|pending|declined|refunded)$")
    card_type: str = Field(default="credit", pattern="^(credit|debit|prepaid)$")


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    merchant_id: int
    amount: Decimal
    currency: str
    status: str
    card_type: str
    created_at: datetime


class Page(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[TransactionOut]


# ---- Analytics ----
class AnalyticsSummary(BaseModel):
    total_volume: Decimal
    transaction_count: int
    approval_rate: float
    avg_ticket: Decimal
    source: str = Field(description="postgres | snowflake — which engine served the query")


class MerchantVolume(BaseModel):
    merchant_id: int
    merchant_name: str
    total_volume: Decimal
    transaction_count: int
