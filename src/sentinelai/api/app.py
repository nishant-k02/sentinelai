from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from sentinelai.api.errors import register_exception_handlers
from sentinelai.api.routes.health import router as health_router
from sentinelai.api.routes.metrics import router as metrics_router
from sentinelai.platform.config import Settings, get_settings
from sentinelai.platform.logging import configure_logging, get_logger


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup/shutdown hook. Phase 0.5 opens DB/Redis pools here and closes
    them on shutdown."""
    log = get_logger(__name__)
    log.info("api_starting")
    yield
    log.info("api_stopping")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Application factory. Production calls this once (see main.py); tests call
    it per test for isolation."""
    settings = settings or get_settings()
    configure_logging(settings)

    app = FastAPI(title="SentinelAI API", version="0.0.0", lifespan=_lifespan)

    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(metrics_router)

    return app
