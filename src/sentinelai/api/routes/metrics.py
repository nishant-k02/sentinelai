from __future__ import annotations

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

router = APIRouter(tags=["observability"])


@router.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    """Prometheus scrape target. Exposes default process/GC collectors now;
    application metrics (request rate, latency, queue depth, token usage)
    arrive from phase 0.8 onward."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
