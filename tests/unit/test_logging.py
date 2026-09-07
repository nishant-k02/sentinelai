import structlog

from sentinelai.platform.config import Settings
from sentinelai.platform.logging import configure_logging, get_logger


def test_json_logging_includes_bound_fields(capsys: object) -> None:
    structlog.reset_defaults()
    configure_logging(Settings(log_json=True, log_level="INFO"))

    get_logger("test").info("incident_created", incident_id="abc123")

    out = capsys.readouterr().out  # type: ignore[attr-defined]
    assert '"event": "incident_created"' in out
    assert '"incident_id": "abc123"' in out
    assert '"service": "sentinelai-api"' in out
    assert '"level": "info"' in out
