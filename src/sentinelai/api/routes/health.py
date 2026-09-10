from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str


class ReadinessResponse(BaseModel):
    status: str
    checks: dict[str, str]


@router.get("/healthz", response_model=HealthResponse)
async def healthz() -> HealthResponse:
    """Liveness — the process is running and the event loop is responsive.
    Kubernetes restarts the pod if this fails."""
    return HealthResponse(status="ok")


@router.get("/readyz", response_model=ReadinessResponse)
async def readyz() -> ReadinessResponse:
    """Readiness — every dependency this process needs is reachable.
    Kubernetes removes the pod from the Service load balancer if this fails,
    without restarting it. Phase 0.5 adds Postgres and Redis checks here."""
    checks: dict[str, str] = {}
    status = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return ReadinessResponse(status=status, checks=checks)
