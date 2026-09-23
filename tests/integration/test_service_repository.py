from __future__ import annotations

import uuid

import pytest

from sentinelai.modules.organization.models import Organization
from sentinelai.modules.service.models import Environment
from sentinelai.modules.service.repository import ServiceRepository
from sentinelai.platform.config import get_settings
from sentinelai.platform.db import create_db_engine, create_session_factory

pytestmark = pytest.mark.integration


async def test_service_repository_lists_filtered_by_org_and_environment() -> None:
    engine = create_db_engine(get_settings())
    session_factory = create_session_factory(engine)
    try:
        async with session_factory() as session:
            org = Organization(name=f"org-{uuid.uuid4()}")
            session.add(org)
            await session.flush()

            repo = ServiceRepository(session)
            await repo.create(
                organization_id=org.id, name="checkout-api", environment=Environment.PRODUCTION
            )
            await repo.create(
                organization_id=org.id, name="billing-api", environment=Environment.STAGING
            )
            await session.commit()

            prod_only = await repo.list(
                organization_id=org.id, environment=Environment.PRODUCTION, limit=50
            )
            assert [s.name for s in prod_only] == ["checkout-api"]

            everything = await repo.list(organization_id=org.id, limit=50)
            assert [s.name for s in everything] == [
                "billing-api",
                "checkout-api",
            ]  # ordered by name
    finally:
        await engine.dispose()
