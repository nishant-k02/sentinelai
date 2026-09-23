from __future__ import annotations

from sentinelai.modules.organization.models import Organization
from sentinelai.platform.repository import SQLAlchemyRepository


class OrganizationRepository(SQLAlchemyRepository[Organization]):
    model = Organization
