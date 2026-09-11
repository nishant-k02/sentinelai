from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    LOCAL = "local"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Process configuration, populated from environment variables.

    Every variable is prefixed ``SENTINEL_`` (e.g. ``SENTINEL_LOG_LEVEL``).
    A local ``.env`` file is read when present; deployed environments inject
    real environment variables instead. Unknown variables are ignored so the
    same ``.env`` can serve several processes.
    """

    model_config = SettingsConfigDict(
        env_prefix="SENTINEL_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Environment = Environment.LOCAL
    service_name: str = "sentinelai-api"
    log_level: str = "INFO"
    # JSON logs everywhere except local dev, where console output reads better.
    log_json: bool = True

    database_url: str = "postgresql+asyncpg://sentinelai:sentinelai@localhost:5432/sentinelai"
    redis_url: str = "redis://localhost:6379/0"

    @property
    def is_local(self) -> bool:
        return self.environment is Environment.LOCAL


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings singleton.

    Cached so environment parsing happens once. Tests call
    ``get_settings.cache_clear()`` before overriding values.
    """
    return Settings()
