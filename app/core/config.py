"""Application configuration via Pydantic settings (12-factor / env-driven)."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- API ---
    app_name: str = "Fintech Analytics Platform"
    api_v1_prefix: str = "/api/v1"
    environment: str = Field(default="development")

    # --- Database (PostgreSQL in prod, SQLite for tests) ---
    database_url: str = Field(
        default="postgresql+asyncpg://finstream:finstream@localhost:5432/finstream",
        description="SQLAlchemy async database URL.",
    )

    # --- Security / Auth ---
    secret_key: str = Field(default="change-me-in-prod-use-a-32+char-random-secret")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # --- CORS (restrictive by default — OWASP A05) ---
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # --- Snowflake (optional; analytics offload when configured) ---
    snowflake_account: str | None = None
    snowflake_user: str | None = None
    snowflake_password: str | None = None
    snowflake_warehouse: str | None = None
    snowflake_database: str | None = None
    snowflake_schema: str | None = None

    @property
    def snowflake_enabled(self) -> bool:
        return all(
            [self.snowflake_account, self.snowflake_user, self.snowflake_password]
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
