from __future__ import annotations

import uuid
from datetime import datetime
from typing import Protocol

from sentinelai.modules.ingestion.models import Deployment, LogEvent, LogLevel, MetricSample
from sentinelai.platform.errors import NotFoundError


class ServiceLookupProtocol(Protocol):
    async def get(self, id: uuid.UUID) -> object | None: ...


class MetricSampleRepositoryProtocol(Protocol):
    async def create(self, **fields: object) -> MetricSample: ...


class LogEventRepositoryProtocol(Protocol):
    async def create(self, **fields: object) -> LogEvent: ...


class DeploymentRepositoryProtocol(Protocol):
    async def create(self, **fields: object) -> Deployment: ...


async def _ensure_service_exists(
    service_repo: ServiceLookupProtocol, service_id: uuid.UUID
) -> None:
    """Every ingestion use case needs this — one query on the hottest write
    path in the system. Caching this (Phase 0.6's get_or_set is built and
    ready) is the obvious next optimization once there's load to justify it;
    not done speculatively here."""
    if await service_repo.get(service_id) is None:
        raise NotFoundError(f"service {service_id} not found")


async def record_metric_sample(
    service_repo: ServiceLookupProtocol,
    metric_repo: MetricSampleRepositoryProtocol,
    *,
    service_id: uuid.UUID,
    metric_name: str,
    value: float,
    recorded_at: datetime,
) -> MetricSample:
    await _ensure_service_exists(service_repo, service_id)
    return await metric_repo.create(
        service_id=service_id, metric_name=metric_name, value=value, recorded_at=recorded_at
    )


async def record_log_event(
    service_repo: ServiceLookupProtocol,
    log_repo: LogEventRepositoryProtocol,
    *,
    service_id: uuid.UUID,
    level: LogLevel,
    message: str,
    attributes: dict[str, object] | None,
    recorded_at: datetime,
) -> LogEvent:
    await _ensure_service_exists(service_repo, service_id)
    return await log_repo.create(
        service_id=service_id,
        level=level,
        message=message,
        attributes=attributes,
        recorded_at=recorded_at,
    )


async def record_deployment(
    service_repo: ServiceLookupProtocol,
    deployment_repo: DeploymentRepositoryProtocol,
    *,
    service_id: uuid.UUID,
    version: str,
    commit_sha: str,
    deployed_by: str,
    deployed_at: datetime,
) -> Deployment:
    await _ensure_service_exists(service_repo, service_id)
    return await deployment_repo.create(
        service_id=service_id,
        version=version,
        commit_sha=commit_sha,
        deployed_by=deployed_by,
        deployed_at=deployed_at,
    )
