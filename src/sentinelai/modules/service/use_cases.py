from __future__ import annotations

import uuid
from typing import Protocol

from sentinelai.modules.service.models import Environment, Service
from sentinelai.platform.errors import ConflictError


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
    repo: ServiceRepositoryProtocol,
    *,
    organization_id: uuid.UUID,
    name: str,
    environment: Environment,
) -> Service:
    """Register a new service.

    Checks for an existing service with this name in this organization
    first, so a legitimate conflict gets a clear 409 (`ConflictError`)
    instead of a raw database `IntegrityError` surfacing as an unhandled
    500. This is a pre-check, not a guarantee — two concurrent
    registrations with the same name can both pass it and race to the
    database. Phase 1.2's unique constraint (and its integration test) is
    the actual backstop that makes duplicates impossible; this check exists
    purely to give the common, non-racing case a better error. The parallel
    to Phase 0.6's `SET NX` vs. `GET`-then-`SET`: an atomic operation at the
    layer that can actually be atomic (the database) is what closes a race
    — a pre-check at a higher layer only improves the common path.
    """
    existing = await repo.get_by_name(organization_id=organization_id, name=name)
    if existing is not None:
        raise ConflictError(f"a service named {name!r} already exists in this organization")
    return await repo.create(organization_id=organization_id, name=name, environment=environment)
