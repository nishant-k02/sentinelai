from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from sentinelai.platform.db import Base


class MetricSample(Base):
    """One immutable, timestamped measurement for a service — never updated
    or deleted through the API (telemetry is append-only, Phase 1.1).

    ``recorded_at`` is when the measurement actually occurred (client-
    supplied — event time); ``created_at`` is when we stored it (server-
    supplied — processing time). They can differ under network delay or a
    backfilled/replayed metric, and that gap is itself useful operational
    data later (ingestion lag), so both are kept rather than collapsed into
    one column.
    """

    __tablename__ = "metric_samples"
    __table_args__ = (
        Index("ix_metric_samples_service_metric_time", "service_id", "metric_name", "recorded_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    service_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("services.id"), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float] = mapped_column(nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LogLevel(StrEnum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogEvent(Base):
    """A structured log line for a service. ``attributes`` is JSONB —
    arbitrary extra fields without a migration per new field, at the cost of
    no type-safety or plain indexing on whatever ends up inside it."""

    __tablename__ = "log_events"
    __table_args__ = (Index("ix_log_events_service_time", "service_id", "recorded_at"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    service_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("services.id"), nullable=False)
    level: Mapped[LogLevel] = mapped_column(SQLEnum(LogLevel, name="log_level"), nullable=False)
    message: Mapped[str] = mapped_column(String(4000), nullable=False)
    attributes: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Deployment(Base):
    """A recorded deployment for a service. ``deployed_by`` is a plain
    string for now — it becomes a real FK to a users table once the
    upcoming Auth milestone introduces one; not worth blocking on today."""

    __tablename__ = "deployments"
    __table_args__ = (Index("ix_deployments_service_time", "service_id", "deployed_at"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    service_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("services.id"), nullable=False)
    version: Mapped[str] = mapped_column(String(100), nullable=False)
    commit_sha: Mapped[str] = mapped_column(String(40), nullable=False)
    deployed_by: Mapped[str] = mapped_column(String(255), nullable=False)
    deployed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
