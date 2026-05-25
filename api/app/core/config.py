"""REGIQ API — Application Configuration (Pydantic Settings)."""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralised application settings loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── App ────────────────────────────────────────────────
    app_name: str = "REGIQ"
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_secret_key: str = "change-me-to-a-random-64-char-string"

    # ── PostgreSQL ─────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://regiq:regiq_dev_password@localhost:5432/regiq"

    # ── MongoDB ────────────────────────────────────────────
    mongo_url: str = "mongodb://localhost:27017/regiq"
    mongo_db: str = "regiq"

    # ── Redis ──────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── JWT ─────────────────────────────────────────────────
    jwt_secret_key: str = "change-me-jwt-secret-key-must-be-at-least-32-chars"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7

    # ── CORS ───────────────────────────────────────────────
    cors_origins: str = "http://localhost:3000,http://localhost:8000"

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
