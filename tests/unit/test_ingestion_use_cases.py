from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from sentinelai.modules.ingestion.use_cases import record_metric_sample
from sentinelai.modules.service.models import Environment
from sentinelai.platform.errors import NotFoundError
from tests.fakes import FakeMetricSampleRepository, FakeServiceRepository


async def test_record_metric_sample_requires_an_existing_service() -> None:
    service_repo = FakeServiceRepository()
    metric_repo = FakeMetricSampleRepository()

    with pytest.raises(NotFoundError):
        await record_metric_sample(
            service_repo,
            metric_repo,
            service_id=uuid.uuid4(),
            metric_name="cpu_percent",
            value=10.0,
            recorded_at=datetime.now(UTC),
        )


async def test_record_metric_sample_succeeds_for_an_existing_service() -> None:
    service_repo = FakeServiceRepository()
    metric_repo = FakeMetricSampleRepository()
    service = await service_repo.create(
        organization_id=uuid.uuid4(), name="svc", environment=Environment.PRODUCTION
    )

    sample = await record_metric_sample(
        service_repo,
        metric_repo,
        service_id=service.id,
        metric_name="cpu_percent",
        value=55.5,
        recorded_at=datetime.now(UTC),
    )
    assert sample.metric_name == "cpu_percent"
