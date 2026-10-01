from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic import model_validator
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
    kafka_bootstrap_servers: str = "localhost:9092"
    otel_exporter_endpoint: str = "http://localhost:4318/v1/traces"
    jwt_secret: str = "insecure-dev-only-secret-change-me"
    jwt_access_token_ttl_seconds: int = 900  # 15 minutes
    jwt_refresh_token_ttl_seconds: int = 60 * 60 * 24 * 7  # 7 days

    @property
    def is_local(self) -> bool:
        return self.environment is Environment.LOCAL

    @model_validator(mode="after")
    def _forbid_weak_jwt_secret_outside_local(self) -> Settings:
        """Fail fast at startup, not silently in production.

        Two checks, not one: the default secret is fine for local dev —
        nothing it protects matters outside your own machine — so the
        first check only fires elsewhere. The second check is broader and
        exists because of a real gap the first one has: a secret that
        isn't the exact default string can still be short and guessable.
        RFC 7518 §3.2 recommends >= 32 bytes for an HS256 signing key;
        PyJWT itself warns (InsecureKeyLengthWarning) below that — this
        turns that warning into a hard failure before the app ever starts,
        rather than a warning buried in logs someone has to notice.
        """
        if not self.is_local:
            if self.jwt_secret == "insecure-dev-only-secret-change-me":
                raise ValueError("SENTINEL_JWT_SECRET must be overridden outside local development")
            if len(self.jwt_secret.encode()) < 32:
                raise ValueError(
                    "SENTINEL_JWT_SECRET must be at least 32 bytes outside local development"
                )
        return self


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings singleton.

    Cached so environment parsing happens once. Tests call
    ``get_settings.cache_clear()`` before overriding values.
    """
    return Settings()
