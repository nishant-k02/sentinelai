from __future__ import annotations

from sqlalchemy import select

from sentinelai.modules.organization.models import Organization
from sentinelai.platform.repository import SQLAlchemyRepository


class OrganizationRepository(SQLAlchemyRepository[Organization]):
    model = Organization

    async def get_by_name(self, name: str) -> Organization | None:
        result = await self._session.execute(select(Organization).where(Organization.name == name))
        return result.scalar_one_or_none()
