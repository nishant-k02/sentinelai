from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, Response, status

from sentinelai.api.deps import OrganizationRepositoryDep, ServiceRepositoryDep
from sentinelai.modules.service.models import Environment
from sentinelai.modules.service.schemas import ServiceCreate, ServiceList, ServiceRead
from sentinelai.modules.service.use_cases import register_service
from sentinelai.platform.errors import NotFoundError

router = APIRouter(prefix="/v1/services", tags=["services"])


@router.post("", response_model=ServiceRead, status_code=status.HTTP_201_CREATED)
async def create_service(
    body: ServiceCreate,
    response: Response,
    org_repo: OrganizationRepositoryDep,
    service_repo: ServiceRepositoryDep,
) -> ServiceRead:
    service = await register_service(
        org_repo,
        service_repo,
        organization_id=body.organization_id,
        name=body.name,
        environment=body.environment,
    )
    response.headers["Location"] = f"/v1/services/{service.id}"
    return ServiceRead.model_validate(service)


@router.get("/{service_id}", response_model=ServiceRead)
async def get_service(service_id: uuid.UUID, repo: ServiceRepositoryDep) -> ServiceRead:
    service = await repo.get(service_id)
    if service is None:
        raise NotFoundError(f"service {service_id} not found")
    return ServiceRead.model_validate(service)


@router.get("", response_model=ServiceList)
async def list_services(
    repo: ServiceRepositoryDep,
    organization_id: uuid.UUID,
    environment: Environment | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> ServiceList:
    items = await repo.list(
        organization_id=organization_id, environment=environment, limit=limit, offset=offset
    )
    total = await repo.count(organization_id=organization_id, environment=environment)
    return ServiceList(
        items=[ServiceRead.model_validate(s) for s in items],
        total=total,
        limit=limit,
        offset=offset,
    )
