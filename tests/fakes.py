from __future__ import annotations

import uuid

from sentinelai.modules.ingestion.models import MetricSample
from sentinelai.modules.organization.models import Organization
from sentinelai.modules.service.models import Environment, Service


class FakeOrganizationRepository:
    """In-memory stand-in for OrganizationRepository — satisfies
    OrganizationLookupProtocol (just `get`), nothing more."""

    def __init__(self) -> None:
        self._by_id: dict[uuid.UUID, Organization] = {}

    async def get(self, id: uuid.UUID) -> Organization | None:
        return self._by_id.get(id)

    async def create(self, **fields: object) -> Organization:
        org = Organization(id=uuid.uuid4(), **fields)
        self._by_id[org.id] = org
        return org


class FakeServiceRepository:
    """An in-memory stand-in for ServiceRepository — same shape
    `register_service` depends on, satisfied structurally, no inheritance,
    no database, no event loop I/O. This is what building against a
    Protocol buys you."""

    def __init__(self) -> None:
        self._by_id: dict[uuid.UUID, Service] = {}

    async def get(self, id: uuid.UUID) -> Service | None:
        return self._by_id.get(id)

    async def create(self, **fields: object) -> Service:
        service = Service(id=uuid.uuid4(), **fields)
        self._by_id[service.id] = service
        return service

    async def list(
        self,
        *,
        organization_id: uuid.UUID,
        environment: Environment | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Service]:
        items = [s for s in self._by_id.values() if s.organization_id == organization_id]
        if environment is not None:
            items = [s for s in items if s.environment == environment]
        items.sort(key=lambda s: s.name)
        return items[offset : offset + limit]

    async def get_by_name(self, *, organization_id: uuid.UUID, name: str) -> Service | None:
        return next(
            (
                s
                for s in self._by_id.values()
                if s.organization_id == organization_id and s.name == name
            ),
            None,
        )


class FakeMetricSampleRepository:
    def __init__(self) -> None:
        self._by_id: dict[uuid.UUID, MetricSample] = {}

    async def get(self, id: uuid.UUID) -> MetricSample | None:
        return self._by_id.get(id)

    async def create(self, **fields: object) -> MetricSample:
        sample = MetricSample(id=uuid.uuid4(), **fields)
        self._by_id[sample.id] = sample
        return sample
