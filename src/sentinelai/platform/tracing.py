from __future__ import annotations

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ALWAYS_ON
from sqlalchemy.ext.asyncio import AsyncEngine

from sentinelai.platform.config import Settings

_tracing_configured = False


def configure_tracing(settings: Settings) -> None:
    """Configure the process-global TracerProvider once, exporting spans via
    OTLP/HTTP to the collector (Jaeger, locally). Call at the start of every
    entrypoint (API, worker).

    Safe to call more than once — a TracerProvider can only be set once per
    process; without this guard, every repeat call (every test that builds a
    fresh app, for instance) would log an "overriding not allowed" warning.

    Sampling is ALWAYS_ON: while building the system we want to see every
    trace. A ratio-based or tail-based sampler is what you switch to once
    traffic volume makes 100% sampling expensive — a phase 0.14-style
    (load testing / cost) concern, not a phase 0.9 one.
    """
    global _tracing_configured
    if _tracing_configured:
        return

    resource = Resource.create(
        {
            SERVICE_NAME: settings.service_name,
            SERVICE_VERSION: "0.0.0",
            "deployment.environment": settings.environment.value,
        }
    )
    provider = TracerProvider(resource=resource, sampler=ALWAYS_ON)
    exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_endpoint)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    _tracing_configured = True


def instrument_sqlalchemy(engine: AsyncEngine) -> None:
    """Every query through `engine` becomes a child span of whatever span is
    active when the query runs. We instrument the sync engine SQLAlchemy's
    async engine wraps internally — that's where the driver calls actually
    happen."""
    SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)


def instrument_redis() -> None:
    """Every redis-py call (sync or async) becomes a child span."""
    RedisInstrumentor().instrument()
