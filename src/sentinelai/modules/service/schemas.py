from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from sentinelai.modules.service.models import Environment


class ServiceCreate(BaseModel):
    # organization_id is client-supplied for now — there's no auth yet to
    # derive it from a JWT claim. Once the Auth milestone lands, this field
    # moves from the request body to being derived from the authenticated
    # principal, and MUST — any caller can currently create services in any
    # organization, which is fine only because nothing is deployed yet.
    organization_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    environment: Environment


class ServiceRead(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    environment: Environment
    created_at: datetime

    model_config = {"from_attributes": True}  # build directly from the ORM instance


class ServiceList(BaseModel):
    items: list[ServiceRead]
    total: int
    limit: int
    offset: int
