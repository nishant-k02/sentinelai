from __future__ import annotations

import logging
import sys

import structlog
from opentelemetry import trace as otel_trace

from sentinelai.platform.config import Settings


def _add_trace_context(
    logger: structlog.types.WrappedLogger,
    method_name: str,
    event_dict: structlog.types.EventDict,
) -> structlog.types.EventDict:
    """Attach trace_id/span_id from whatever OTel span is active right now.
    This is what makes 'find every log line for this one request' possible —
    grep the trace_id from a Jaeger trace, or vice versa."""
    span_ctx = otel_trace.get_current_span().get_span_context()
    if span_ctx.is_valid:
        event_dict["trace_id"] = format(span_ctx.trace_id, "032x")
        event_dict["span_id"] = format(span_ctx.span_id, "016x")
    return event_dict


def configure_logging(settings: Settings) -> None:
    """Configure structlog + stdlib logging for the whole process.

    Call exactly once, at the start of each entrypoint (API, worker).
    Emits JSON in deployed environments and coloured console output locally.
    Binds ``service`` and ``environment`` onto every log line; ``trace_id``
    is added per-request once tracing is wired (phase 0.8).
    """
    level = logging.getLevelNamesMapping().get(settings.log_level.upper(), logging.INFO)

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        _add_trace_context,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    renderer: structlog.types.Processor = (
        structlog.processors.JSONRenderer()
        if settings.log_json
        else structlog.dev.ConsoleRenderer(colors=True)
    )

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    structlog.contextvars.bind_contextvars(
        service=settings.service_name,
        environment=settings.environment.value,
    )

    # Route stdlib logging (uvicorn, sqlalchemy, alembic) through the same stream.
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a bound logger. Pass ``__name__`` from the calling module."""
    logger: structlog.stdlib.BoundLogger = structlog.get_logger(name)
    return logger
