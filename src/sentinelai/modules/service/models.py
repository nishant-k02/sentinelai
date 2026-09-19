from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from sentinelai.platform.db import Base


class Environment(StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Service(Base):
    """A monitored service, scoped to one organization. Everything else in
    this milestone - metrics, logs, deployments - hangs off a Service.

    The FK below references the ``organizations`` table by name, not by
    importing the Organization class - modules stay independent in Python
    even though their tables relate at the database level. See ADR (this
    phase's commit) and the import-linter "independent modules" contract.
    """

    __tablename__ = "services"
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_services_organization_id_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    environment: Mapped[Environment] = mapped_column(
        SQLEnum(Environment, name="environment"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
