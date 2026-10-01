import pytest
from pydantic_core import ValidationError

from sentinelai.platform.config import Environment, Settings


def test_defaults_are_local() -> None:
    settings = Settings()
    assert settings.environment is Environment.LOCAL
    assert settings.service_name == "sentinelai-api"
    assert settings.is_local is True


def test_env_vars_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SENTINEL_ENVIRONMENT", "production")
    monkeypatch.setenv("SENTINEL_LOG_LEVEL", "WARNING")
    monkeypatch.setenv("SENTINEL_JWT_SECRET", "a-sufficiently-long-production-grade-secret-value")
    settings = Settings()
    assert settings.environment is Environment.PRODUCTION
    assert settings.is_local is False
    assert settings.log_level == "WARNING"


def test_production_requires_a_real_jwt_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SENTINEL_ENVIRONMENT", "production")
    with pytest.raises(ValidationError):
        Settings()


def test_production_rejects_a_short_but_non_default_jwt_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SENTINEL_ENVIRONMENT", "production")
    monkeypatch.setenv("SENTINEL_JWT_SECRET", "short-secret")  # not the default, still too weak
    with pytest.raises(ValidationError):
        Settings()
