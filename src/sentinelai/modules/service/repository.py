from __future__ import annotations

import uuid

from sqlalchemy import func, select

from sentinelai.modules.service.models import Environment, Service
from sentinelai.platform.repository import SQLAlchemyRepository


class ServiceRepository(SQLAlchemyRepository[Service]):
    model = Service

    async def list(
        self,
        *,
        organization_id: uuid.UUID,
        environment: Environment | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Service]:
        stmt = select(Service).where(Service.organization_id == organization_id)
        if environment is not None:
            stmt = stmt.where(Service.environment == environment)
        stmt = stmt.order_by(Service.name).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_name(self, *, organization_id: uuid.UUID, name: str) -> Service | None:
        stmt = select(Service).where(
            Service.organization_id == organization_id, Service.name == name
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def count(
        self, *, organization_id: uuid.UUID, environment: Environment | None = None
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(Service)
            .where(Service.organization_id == organization_id)
        )
        if environment is not None:
            stmt = stmt.where(Service.environment == environment)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())
