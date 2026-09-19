import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from sentinelai.modules.ingestion.models import Deployment, LogEvent, LogLevel, MetricSample
from sentinelai.modules.organization.models import Organization
from sentinelai.modules.service.models import Environment, Service
from sentinelai.platform.config import get_settings
from sentinelai.platform.db import create_db_engine, create_session_factory

pytestmark = pytest.mark.integration


@pytest.fixture
async def session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_db_engine(get_settings())
    factory = create_session_factory(engine)
    yield factory
    await engine.dispose()


async def test_duplicate_service_name_in_same_org_is_rejected(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        org = Organization(name=f"org-{uuid.uuid4()}")
        session.add(org)
        await session.flush()

        session.add(
            Service(organization_id=org.id, name="checkout-api", environment=Environment.PRODUCTION)
        )
        await session.commit()

        session.add(
            Service(organization_id=org.id, name="checkout-api", environment=Environment.STAGING)
        )
        with pytest.raises(IntegrityError):
            await session.commit()
        await session.rollback()


async def test_metric_sample_requires_a_real_service(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        session.add(
            MetricSample(
                service_id=uuid.uuid4(),  # no such service exists
                metric_name="cpu_percent",
                value=42.0,
                recorded_at=datetime.now(UTC),
            )
        )
        with pytest.raises(IntegrityError):
            await session.commit()
        await session.rollback()


async def test_log_event_and_deployment_persist_correctly(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        org = Organization(name=f"org-{uuid.uuid4()}")
        session.add(org)
        await session.flush()
        service = Service(
            organization_id=org.id, name=f"svc-{uuid.uuid4()}", environment=Environment.STAGING
        )
        session.add(service)
        await session.flush()

        session.add(
            LogEvent(
                service_id=service.id,
                level=LogLevel.ERROR,
                message="database connection refused",
                attributes={"retry_count": 3},
                recorded_at=datetime.now(UTC),
            )
        )
        session.add(
            Deployment(
                service_id=service.id,
                version="1.4.0",
                commit_sha="a" * 40,
                deployed_by="nishant",
                deployed_at=datetime.now(UTC),
            )
        )
        await session.commit()
