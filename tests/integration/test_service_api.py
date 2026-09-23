from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from tests.helpers import make_organization

pytestmark = pytest.mark.integration


async def test_create_get_list_service(live_client: AsyncClient) -> None:
    org_id = await make_organization()

    create_resp = await live_client.post(
        "/v1/services",
        json={"organization_id": str(org_id), "name": "checkout-api", "environment": "production"},
    )
    assert create_resp.status_code == 201
    assert create_resp.headers["location"].startswith("/v1/services/")
    created = create_resp.json()

    get_resp = await live_client.get(f"/v1/services/{created['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == created["id"]

    list_resp = await live_client.get("/v1/services", params={"organization_id": str(org_id)})
    assert list_resp.status_code == 200
    body = list_resp.json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == "checkout-api"


async def test_duplicate_service_name_returns_409(live_client: AsyncClient) -> None:
    org_id = await make_organization()
    payload = {"organization_id": str(org_id), "name": "billing-api", "environment": "staging"}

    assert (await live_client.post("/v1/services", json=payload)).status_code == 201

    second = await live_client.post("/v1/services", json=payload)
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "conflict"


async def test_get_unknown_service_returns_404(live_client: AsyncClient) -> None:
    resp = await live_client.get(f"/v1/services/{uuid.uuid4()}")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


async def test_missing_required_field_returns_our_error_envelope(live_client: AsyncClient) -> None:
    resp = await live_client.post("/v1/services", json={"organization_id": str(uuid.uuid4())})
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["code"] == "validation_error"
    assert "name" in body["error"]["message"]
