from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from sentinelai.modules.ingestion.repository import (
    DeploymentRepository,
    LogEventRepository,
    MetricSampleRepository,
)
from sentinelai.modules.service.repository import ServiceRepository
from sentinelai.platform.errors import RateLimitExceededError
from sentinelai.platform.rate_limit import is_allowed


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """One session per request — one transaction boundary per request.
    Commits if the route completes without raising; rolls back and
    re-raises otherwise, so our exception handlers (Phase 0.4) still see
    whatever went wrong."""
    session_factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_service_repository(session: SessionDep) -> ServiceRepository:
    return ServiceRepository(session)


ServiceRepositoryDep = Annotated[ServiceRepository, Depends(get_service_repository)]


async def get_metric_sample_repository(session: SessionDep) -> MetricSampleRepository:
    return MetricSampleRepository(session)


MetricSampleRepositoryDep = Annotated[MetricSampleRepository, Depends(get_metric_sample_repository)]


async def get_log_event_repository(session: SessionDep) -> LogEventRepository:
    return LogEventRepository(session)


LogEventRepositoryDep = Annotated[LogEventRepository, Depends(get_log_event_repository)]


async def get_deployment_repository(session: SessionDep) -> DeploymentRepository:
    return DeploymentRepository(session)


DeploymentRepositoryDep = Annotated[DeploymentRepository, Depends(get_deployment_repository)]


def get_redis(request: Request) -> Redis:
    redis: Redis = request.app.state.redis
    return redis


RedisDep = Annotated[Redis, Depends(get_redis)]


async def enforce_ingestion_rate_limit(service_id: uuid.UUID, redis: RedisDep) -> None:
    """Cap ingestion writes per service. 1000 samples/min is a generous,
    unvalidated ceiling for M1 — a real number comes from load testing
    (Phase M14), not a guess; this exists to prove the mechanism works."""
    allowed = await is_allowed(
        redis, f"ratelimit:ingest:{service_id}", limit=1000, window_seconds=60
    )
    if not allowed:
        raise RateLimitExceededError(f"ingestion rate limit exceeded for service {service_id}")


RateLimitDep = Annotated[None, Depends(enforce_ingestion_rate_limit)]
