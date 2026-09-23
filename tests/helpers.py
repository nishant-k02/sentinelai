from __future__ import annotations

import uuid

from sentinelai.modules.organization.models import Organization
from sentinelai.modules.service.models import Environment, Service
from sentinelai.platform.config import get_settings
from sentinelai.platform.db import create_db_engine, create_session_factory


async def make_organization() -> uuid.UUID:
    engine = create_db_engine(get_settings())
    session_factory = create_session_factory(engine)
    try:
        async with session_factory() as session:
            org = Organization(name=f"org-{uuid.uuid4()}")
            session.add(org)
            await session.commit()
            return org.id
    finally:
        await engine.dispose()


async def make_service(organization_id: uuid.UUID) -> uuid.UUID:
    engine = create_db_engine(get_settings())
    session_factory = create_session_factory(engine)
    try:
        async with session_factory() as session:
            service = Service(
                organization_id=organization_id,
                name=f"svc-{uuid.uuid4()}",
                environment=Environment.PRODUCTION,
            )
            session.add(service)
            await session.commit()
            return service.id
    finally:
        await engine.dispose()
