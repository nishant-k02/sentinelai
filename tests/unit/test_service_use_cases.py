from __future__ import annotations

import uuid

import pytest

from sentinelai.modules.service.models import Environment
from sentinelai.modules.service.use_cases import register_service
from sentinelai.platform.errors import ConflictError
from tests.fakes import FakeServiceRepository


async def test_register_service_creates_it() -> None:
    repo = FakeServiceRepository()
    org_id = uuid.uuid4()

    service = await register_service(
        repo, organization_id=org_id, name="checkout-api", environment=Environment.PRODUCTION
    )

    assert service.name == "checkout-api"
    assert service.environment is Environment.PRODUCTION
    assert await repo.get(service.id) is service


async def test_register_service_rejects_duplicate_name_in_same_org() -> None:
    repo = FakeServiceRepository()
    org_id = uuid.uuid4()
    await register_service(
        repo, organization_id=org_id, name="checkout-api", environment=Environment.PRODUCTION
    )

    with pytest.raises(ConflictError):
        await register_service(
            repo, organization_id=org_id, name="checkout-api", environment=Environment.STAGING
        )


async def test_register_service_allows_same_name_in_different_orgs() -> None:
    repo = FakeServiceRepository()
    await register_service(
        repo, organization_id=uuid.uuid4(), name="checkout-api", environment=Environment.PRODUCTION
    )

    service = await register_service(
        repo, organization_id=uuid.uuid4(), name="checkout-api", environment=Environment.PRODUCTION
    )
    assert service.name == "checkout-api"
