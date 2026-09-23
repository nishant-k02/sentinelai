from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from sentinelai.platform.config import get_settings
from sentinelai.platform.redis import create_redis
from tests.helpers import make_organization, make_service

pytestmark = pytest.mark.integration


async def test_ingest_metric_log_deployment(live_client: AsyncClient) -> None:
    service_id = await make_service(await make_organization())

    metric_resp = await live_client.post(
        f"/v1/services/{service_id}/metrics",
        json={"metric_name": "cpu_percent", "value": 42.0, "recorded_at": "2026-01-01T00:00:00Z"},
    )
    assert metric_resp.status_code == 201

    log_resp = await live_client.post(
        f"/v1/services/{service_id}/logs",
        json={"level": "error", "message": "boom", "recorded_at": "2026-01-01T00:00:00Z"},
    )
    assert log_resp.status_code == 201

    deploy_resp = await live_client.post(
        f"/v1/services/{service_id}/deployments",
        json={
            "version": "1.0.0",
            "commit_sha": "a" * 40,
            "deployed_by": "nishant",
            "deployed_at": "2026-01-01T00:00:00Z",
        },
    )
    assert deploy_resp.status_code == 201


async def test_ingest_metric_against_unknown_service_returns_404(live_client: AsyncClient) -> None:
    resp = await live_client.post(
        f"/v1/services/{uuid.uuid4()}/metrics",
        json={"metric_name": "cpu_percent", "value": 1.0, "recorded_at": "2026-01-01T00:00:00Z"},
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


async def test_metrics_keyset_pagination_covers_all_rows_without_duplicates(
    live_client: AsyncClient,
) -> None:
    service_id = await make_service(await make_organization())
    for i in range(5):
        resp = await live_client.post(
            f"/v1/services/{service_id}/metrics",
            json={
                "metric_name": "cpu_percent",
                "value": float(i),
                "recorded_at": f"2026-01-01T00:0{i}:00Z",
            },
        )
        assert resp.status_code == 201

    seen_ids: set[str] = set()
    cursor: str | None = None
    pages = 0
    while True:
        params: dict[str, str | int] = {"limit": 2}
        if cursor:
            params["cursor"] = cursor
        resp = await live_client.get(f"/v1/services/{service_id}/metrics", params=params)
        assert resp.status_code == 200
        body = resp.json()
        seen_ids.update(item["id"] for item in body["items"])
        pages += 1
        cursor = body["next_cursor"]
        if cursor is None:
            break
        assert pages < 10  # safety valve — a pagination bug should fail fast, not hang the suite

    assert len(seen_ids) == 5


async def test_ingest_metric_returns_429_when_rate_limited(live_client: AsyncClient) -> None:
    """Pre-seed the counter at the limit instead of sending 1000 real
    requests — tests the wiring (dependency -> is_allowed -> 429), not
    is_allowed itself (already proven in Phase 0.6)."""
    service_id = await make_service(await make_organization())
    redis = create_redis(get_settings())
    key = f"ratelimit:ingest:{service_id}"
    try:
        await redis.set(key, "1000", ex=60)
        resp = await live_client.post(
            f"/v1/services/{service_id}/metrics",
            json={
                "metric_name": "cpu_percent",
                "value": 1.0,
                "recorded_at": "2026-01-01T00:00:00Z",
            },
        )
        assert resp.status_code == 429
        assert resp.json()["error"]["code"] == "rate_limit_exceeded"
    finally:
        await redis.delete(key)
        await redis.aclose()
