from collections.abc import AsyncIterator, Iterator

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from sentinelai.api.app import create_app
from sentinelai.platform.config import get_settings


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> Iterator[None]:
    """Clear cached Settings around every test so env overrides take effect."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """App WITHOUT lifespan — fast, for endpoints that need no backing services."""
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def live_client() -> AsyncIterator[AsyncClient]:
    """App WITH lifespan active (real engine + Redis on app.state).
    Requires `make up`. Integration tests only."""
    app = create_app()
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c
