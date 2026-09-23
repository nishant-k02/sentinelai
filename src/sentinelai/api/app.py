from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from sentinelai.api.errors import register_exception_handlers
from sentinelai.api.routes.health import router as health_router
from sentinelai.api.routes.ingestion import router as ingestion_router
from sentinelai.api.routes.metrics import router as metrics_router
from sentinelai.api.routes.services import router as services_router
from sentinelai.platform.config import Settings, get_settings
from sentinelai.platform.db import create_db_engine, create_session_factory
from sentinelai.platform.logging import configure_logging, get_logger
from sentinelai.platform.redis import create_redis
from sentinelai.platform.tracing import configure_tracing, instrument_redis, instrument_sqlalchemy


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Runs once around the server's life. Open pools here; close them on exit."""
    log = get_logger(__name__)
    settings: Settings = app.state.settings

    engine = create_db_engine(settings)
    redis = create_redis(settings)
    instrument_sqlalchemy(engine)
    instrument_redis()
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)
    app.state.redis = redis
    log.info("api_started")

    try:
        yield
    finally:
        await engine.dispose()
        await redis.aclose()
        log.info("api_stopped")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Application factory. Prod calls it once; tests call it per test."""
    settings = settings or get_settings()
    configure_logging(settings)
    configure_tracing(settings)

    app = FastAPI(title="SentinelAI API", version="0.0.0", lifespan=_lifespan)
    app.state.settings = settings

    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(metrics_router)
    app.include_router(services_router)
    app.include_router(ingestion_router)
    FastAPIInstrumentor.instrument_app(app)
    return app
