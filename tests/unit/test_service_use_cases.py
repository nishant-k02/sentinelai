from __future__ import annotations

import uuid

import pytest

from sentinelai.modules.service.models import Environment
from sentinelai.modules.service.use_cases import register_service
from sentinelai.platform.errors import ConflictError, NotFoundError
from tests.fakes import FakeOrganizationRepository, FakeServiceRepository


async def test_register_service_rejects_unknown_organization() -> None:
    org_repo = FakeOrganizationRepository()
    service_repo = FakeServiceRepository()

    with pytest.raises(NotFoundError):
        await register_service(
            org_repo,
            service_repo,
            organization_id=uuid.uuid4(),  # never created in org_repo
            name="checkout-api",
            environment=Environment.PRODUCTION,
        )


async def test_register_service_creates_it() -> None:
    org_repo = FakeOrganizationRepository()
    service_repo = FakeServiceRepository()
    org = await org_repo.create(name="acme")

    service = await register_service(
        org_repo,
        service_repo,
        organization_id=org.id,
        name="checkout-api",
        environment=Environment.PRODUCTION,
    )

    assert service.name == "checkout-api"
    assert service.environment is Environment.PRODUCTION
    assert await service_repo.get(service.id) is service


async def test_register_service_rejects_duplicate_name_in_same_org() -> None:
    org_repo = FakeOrganizationRepository()
    service_repo = FakeServiceRepository()
    org = await org_repo.create(name="acme")
    await register_service(
        org_repo,
        service_repo,
        organization_id=org.id,
        name="checkout-api",
        environment=Environment.PRODUCTION,
    )

    with pytest.raises(ConflictError):
        await register_service(
            org_repo,
            service_repo,
            organization_id=org.id,
            name="checkout-api",
            environment=Environment.STAGING,
        )


async def test_register_service_allows_same_name_in_different_orgs() -> None:
    org_repo = FakeOrganizationRepository()
    service_repo = FakeServiceRepository()
    org_a = await org_repo.create(name="acme")
    org_b = await org_repo.create(name="globex")

    await register_service(
        org_repo,
        service_repo,
        organization_id=org_a.id,
        name="checkout-api",
        environment=Environment.PRODUCTION,
    )
    service = await register_service(
        org_repo,
        service_repo,
        organization_id=org_b.id,
        name="checkout-api",
        environment=Environment.PRODUCTION,
    )

    assert service.name == "checkout-api"
