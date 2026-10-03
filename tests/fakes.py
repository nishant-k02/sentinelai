from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sentinelai.modules.auth.models import RefreshToken, User
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


class FakeUserRepository:
    def __init__(self) -> None:
        self._by_id: dict[uuid.UUID, User] = {}

    async def get(self, id: uuid.UUID) -> User | None:
        return self._by_id.get(id)

    async def get_by_email(self, email: str) -> User | None:
        return next((u for u in self._by_id.values() if u.email == email), None)

    async def create(self, **fields: object) -> User:
        user = User(id=uuid.uuid4(), **fields)
        self._by_id[user.id] = user
        return user


class FakeRefreshTokenRepository:
    def __init__(self) -> None:
        self._by_id: dict[uuid.UUID, RefreshToken] = {}

    async def create(self, **fields: object) -> RefreshToken:
        token = RefreshToken(id=uuid.uuid4(), revoked_at=None, **fields)
        self._by_id[token.id] = token
        return token

    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        return next((t for t in self._by_id.values() if t.token_hash == token_hash), None)

    async def revoke_if_active(self, token_id: uuid.UUID) -> bool:
        token = self._by_id.get(token_id)
        if token is None or token.revoked_at is not None:
            return False
        token.revoked_at = datetime.now(UTC)
        return True

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        for token in self._by_id.values():
            if token.user_id == user_id and token.revoked_at is None:
                token.revoked_at = datetime.now(UTC)
