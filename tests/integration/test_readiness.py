import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration


async def test_readyz_reports_all_dependencies_up(live_client: AsyncClient) -> None:
    resp = await live_client.get("/readyz")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["checks"] == {"postgres": "ok", "redis": "ok"}
