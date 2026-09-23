from __future__ import annotations

import uuid
from typing import Protocol

from sentinelai.modules.service.models import Environment, Service
from sentinelai.platform.errors import ConflictError, NotFoundError


class OrganizationLookupProtocol(Protocol):
    """Only what this use case needs to verify: does an organization with
    this id exist. Found missing during Phase 1.6 acceptance testing — see
    the note on `register_service` below."""

    async def get(self, id: uuid.UUID) -> object | None: ...


class ServiceRepositoryProtocol(Protocol):
    """The exact shape `register_service` needs — defined by the consumer,
    not by the repository. `ServiceRepository` and, in tests, a fake both
    satisfy this structurally, without either knowing the other exists.
    This is Dependency Inversion in practice: the high-level policy (this
    function) owns the interface it depends on; the low-level details
    (a real or fake repository) conform to it, not the reverse."""

    async def get_by_name(self, *, organization_id: uuid.UUID, name: str) -> Service | None: ...
    async def create(self, **fields: object) -> Service: ...


async def register_service(
    org_repo: OrganizationLookupProtocol,
    service_repo: ServiceRepositoryProtocol,
    *,
    organization_id: uuid.UUID,
    name: str,
    environment: Environment,
) -> Service:
    """Register a new service.

    Checks the organization actually exists first — a bogus organization_id
    reaching the database is a foreign-key violation (`IntegrityError`),
    which isn't a `SentinelError` and would otherwise surface as an
    unhandled 500. Caught during Phase 1.6 manual acceptance testing: every
    automated test up to this point happened to create a real organization
    first, so this gap was invisible to the whole suite.

    Then checks for an existing service with this name in this organization,
    so a legitimate conflict gets a clear 409 (`ConflictError`) instead of a
    raw database `IntegrityError`. This second check is a pre-check, not a
    guarantee — two concurrent registrations with the same name can both
    pass it and race to the database. Phase 1.2's unique constraint (and its
    integration test) is the actual backstop that makes duplicates
    impossible; this check exists purely to give the common, non-racing case
    a better error. The parallel to Phase 0.6's `SET NX` vs. `GET`-then-`SET`:
    an atomic operation at the layer that can actually be atomic (the
    database) is what closes a race — a pre-check at a higher layer only
    improves the common path.
    """
    if await org_repo.get(organization_id) is None:
        raise NotFoundError(f"organization {organization_id} not found")

    existing = await service_repo.get_by_name(organization_id=organization_id, name=name)
    if existing is not None:
        raise ConflictError(f"a service named {name!r} already exists in this organization")
    return await service_repo.create(
        organization_id=organization_id, name=name, environment=environment
    )
