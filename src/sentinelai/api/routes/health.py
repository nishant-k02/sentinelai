from __future__ import annotations

from fastapi import APIRouter, Request, Response, status
from pydantic import BaseModel
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str


class ReadinessResponse(BaseModel):
    status: str
    checks: dict[str, str]


@router.get("/healthz", response_model=HealthResponse)
async def healthz() -> HealthResponse:
    """Liveness: the process runs and the event loop responds. No I/O.
    A failure here means 'restart the pod'."""
    return HealthResponse(status="ok")


@router.get("/readyz", response_model=ReadinessResponse)
async def readyz(request: Request, response: Response) -> ReadinessResponse:
    """Readiness: every backing service this pod needs is reachable.
    A failure here means 'stop sending traffic' — but do NOT restart."""
    checks: dict[str, str] = {}

    try:
        async with request.app.state.engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except (SQLAlchemyError, OSError) as exc:
        checks["postgres"] = f"error: {type(exc).__name__}"

    try:
        await request.app.state.redis.ping()
        checks["redis"] = "ok"
    except (RedisError, OSError) as exc:
        checks["redis"] = f"error: {type(exc).__name__}"

    ready = all(v == "ok" for v in checks.values())
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(status="ok" if ready else "degraded", checks=checks)
