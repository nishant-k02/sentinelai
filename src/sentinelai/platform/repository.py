from __future__ import annotations

import uuid
from typing import Any, ClassVar, Protocol

from sqlalchemy.ext.asyncio import AsyncSession


class Repository[ModelT](Protocol):
    """The persistence shape every module's repository provides at minimum:
    look up by id, create a new record. Deliberately NOT full CRUD — `list`
    is excluded on purpose (Phase 1.1): every entity's listing needs differ
    enough — offset vs. keyset pagination, different filters — that one
    shared `list` signature would either be wrong for some entity or too
    watered-down to mean anything. Concrete repositories add whatever
    list/query methods their entity actually needs.
    """

    async def get(self, id: uuid.UUID) -> ModelT | None: ...
    async def create(self, **fields: object) -> ModelT: ...


class SQLAlchemyRepository[ModelT]:
    """Base for SQLAlchemy-backed repositories. Subclasses set `model` and
    add entity-specific query methods; `get`/`create` are implemented once,
    here, generically — every future repository (metrics, logs, deployments,
    and beyond) gets these for free instead of reimplementing them."""

    model: ClassVar[type[Any]]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: uuid.UUID) -> ModelT | None:
        return await self._session.get(self.model, id)

    async def create(self, **fields: object) -> ModelT:
        instance = self.model(**fields)
        self._session.add(instance)
        await self._session.flush()
        return instance  # type: ignore[no-any-return]
