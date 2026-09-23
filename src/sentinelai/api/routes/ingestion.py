from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, Response, status

from sentinelai.api.deps import (
    DeploymentRepositoryDep,
    LogEventRepositoryDep,
    MetricSampleRepositoryDep,
    RateLimitDep,
    ServiceRepositoryDep,
)
from sentinelai.modules.ingestion.schemas import (
    DeploymentCreate,
    DeploymentRead,
    LogEventCreate,
    LogEventRead,
    MetricSampleCreate,
    MetricSampleList,
    MetricSampleRead,
)
from sentinelai.modules.ingestion.use_cases import (
    record_deployment,
    record_log_event,
    record_metric_sample,
)
from sentinelai.platform.pagination import decode_cursor, encode_cursor

router = APIRouter(prefix="/v1/services/{service_id}", tags=["ingestion"])


@router.post("/metrics", response_model=MetricSampleRead, status_code=status.HTTP_201_CREATED)
async def ingest_metric(
    service_id: uuid.UUID,
    body: MetricSampleCreate,
    response: Response,
    service_repo: ServiceRepositoryDep,
    metric_repo: MetricSampleRepositoryDep,
    _rate_limit: RateLimitDep,
) -> MetricSampleRead:
    sample = await record_metric_sample(
        service_repo,
        metric_repo,
        service_id=service_id,
        metric_name=body.metric_name,
        value=body.value,
        recorded_at=body.recorded_at,
    )
    response.headers["Location"] = f"/v1/services/{service_id}/metrics/{sample.id}"
    return MetricSampleRead.model_validate(sample)


@router.get("/metrics", response_model=MetricSampleList)
async def list_metrics(
    service_id: uuid.UUID,
    metric_repo: MetricSampleRepositoryDep,
    metric_name: str | None = None,
    cursor: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> MetricSampleList:
    decoded = decode_cursor(cursor) if cursor is not None else None
    # Fetch one extra to know whether another page exists, without a
    # separate COUNT — the standard keyset-pagination technique, and the
    # reason "total" isn't a field on this response the way it is on
    # /v1/services: it's not a cheap or even meaningful question to ask of
    # an endlessly-growing stream.
    fetched = await metric_repo.list_for_service(
        service_id=service_id, metric_name=metric_name, limit=limit + 1, cursor=decoded
    )
    has_more = len(fetched) > limit
    items = fetched[:limit]
    next_cursor = encode_cursor(items[-1].recorded_at, items[-1].id) if has_more and items else None
    return MetricSampleList(
        items=[MetricSampleRead.model_validate(m) for m in items], next_cursor=next_cursor
    )


@router.post("/logs", response_model=LogEventRead, status_code=status.HTTP_201_CREATED)
async def ingest_log(
    service_id: uuid.UUID,
    body: LogEventCreate,
    response: Response,
    service_repo: ServiceRepositoryDep,
    log_repo: LogEventRepositoryDep,
    _rate_limit: RateLimitDep,
) -> LogEventRead:
    event = await record_log_event(
        service_repo,
        log_repo,
        service_id=service_id,
        level=body.level,
        message=body.message,
        attributes=body.attributes,
        recorded_at=body.recorded_at,
    )
    response.headers["Location"] = f"/v1/services/{service_id}/logs/{event.id}"
    return LogEventRead.model_validate(event)


@router.post("/deployments", response_model=DeploymentRead, status_code=status.HTTP_201_CREATED)
async def ingest_deployment(
    service_id: uuid.UUID,
    body: DeploymentCreate,
    response: Response,
    service_repo: ServiceRepositoryDep,
    deployment_repo: DeploymentRepositoryDep,
) -> DeploymentRead:
    # Deliberately no RateLimitDep here — deployments are rare, human/CI-
    # triggered events, not a high-volume path an abuse-prevention limit
    # needs to guard. Not every write endpoint needs rate limiting.
    deployment = await record_deployment(
        service_repo,
        deployment_repo,
        service_id=service_id,
        version=body.version,
        commit_sha=body.commit_sha,
        deployed_by=body.deployed_by,
        deployed_at=body.deployed_at,
    )
    response.headers["Location"] = f"/v1/services/{service_id}/deployments/{deployment.id}"
    return DeploymentRead.model_validate(deployment)
