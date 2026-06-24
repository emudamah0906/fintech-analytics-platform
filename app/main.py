"""FastAPI application entrypoint."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.base import Base
from app.db.session import engine
from app.middleware import RequestContextMiddleware


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    # Auto-create tables for local/dev convenience. Use Alembic migrations in prod.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description=(
        "Global fintech financial-analytics API. FastAPI microservice over "
        "PostgreSQL + Snowflake, with JWT/OAuth2 auth and role-based access control."
    ),
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["system"], summary="Liveness probe")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__, "environment": settings.environment}
