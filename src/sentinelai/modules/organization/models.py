from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from sentinelai.platform.db import Base


class Organization(Base):
    """The top-level tenant. Every user, project, service, and incident will
    eventually hang off an organization (multi-tenancy arrives post-MVP; the
    column is here from the start so it's never a painful backfill)."""

    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
