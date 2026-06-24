"""Aggregate v1 router — single mount point for versioned API."""
from fastapi import APIRouter

from app.api.v1 import analytics, auth, transactions

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(transactions.router)
api_router.include_router(analytics.router)
