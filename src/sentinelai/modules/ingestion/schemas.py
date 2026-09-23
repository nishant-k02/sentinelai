from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from sentinelai.modules.ingestion.models import LogLevel


class MetricSampleCreate(BaseModel):
    metric_name: str = Field(min_length=1, max_length=100)
    value: float
    recorded_at: datetime


class MetricSampleRead(BaseModel):
    id: uuid.UUID
    service_id: uuid.UUID
    metric_name: str
    value: float
    recorded_at: datetime
    created_at: datetime
    model_config = {"from_attributes": True}


class MetricSampleList(BaseModel):
    items: list[MetricSampleRead]
    next_cursor: str | None


class LogEventCreate(BaseModel):
    level: LogLevel
    message: str = Field(min_length=1, max_length=4000)
    attributes: dict[str, object] | None = None
    recorded_at: datetime


class LogEventRead(BaseModel):
    id: uuid.UUID
    service_id: uuid.UUID
    level: LogLevel
    message: str
    attributes: dict[str, object] | None
    recorded_at: datetime
    created_at: datetime
    model_config = {"from_attributes": True}


class DeploymentCreate(BaseModel):
    version: str = Field(min_length=1, max_length=100)
    commit_sha: str = Field(min_length=7, max_length=40)
    deployed_by: str = Field(min_length=1, max_length=255)
    deployed_at: datetime


class DeploymentRead(BaseModel):
    id: uuid.UUID
    service_id: uuid.UUID
    version: str
    commit_sha: str
    deployed_by: str
    deployed_at: datetime
    created_at: datetime
    model_config = {"from_attributes": True}
