import pytest

from sentinelai.platform.config import Environment, Settings, get_settings


def test_defaults_are_local() -> None:
    settings = Settings()
    assert settings.environment is Environment.LOCAL
    assert settings.service_name == "sentinelai-api"
    assert settings.is_local is True


def test_env_vars_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SENTINEL_ENVIRONMENT", "production")
    monkeypatch.setenv("SENTINEL_LOG_LEVEL", "WARNING")
    settings = Settings()
    assert settings.environment is Environment.PRODUCTION
    assert settings.is_local is False
    assert settings.log_level == "WARNING"


def test_get_settings_is_cached() -> None:
    assert get_settings() is get_settings()
