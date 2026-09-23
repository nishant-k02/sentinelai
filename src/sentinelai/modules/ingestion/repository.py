from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select, tuple_

from sentinelai.modules.ingestion.models import Deployment, LogEvent, MetricSample
from sentinelai.platform.repository import SQLAlchemyRepository


class MetricSampleRepository(SQLAlchemyRepository[MetricSample]):
    model = MetricSample

    async def list_for_service(
        self,
        *,
        service_id: uuid.UUID,
        metric_name: str | None = None,
        limit: int = 100,
        cursor: tuple[datetime, uuid.UUID] | None = None,
    ) -> list[MetricSample]:
        stmt = select(MetricSample).where(MetricSample.service_id == service_id)
        if metric_name is not None:
            stmt = stmt.where(MetricSample.metric_name == metric_name)
        if cursor is not None:
            recorded_at, id_ = cursor
            # Row-value comparison — the actual SQL mechanism behind keyset
            # pagination: seek past everything <= the cursor's sort key in
            # one indexed comparison, not a re-derived OFFSET.
            stmt = stmt.where(
                tuple_(MetricSample.recorded_at, MetricSample.id) < (recorded_at, id_)
            )
        stmt = stmt.order_by(MetricSample.recorded_at.desc(), MetricSample.id.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


class LogEventRepository(SQLAlchemyRepository[LogEvent]):
    model = LogEvent


class DeploymentRepository(SQLAlchemyRepository[Deployment]):
    model = Deployment
