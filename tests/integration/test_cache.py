import pytest

from sentinelai.platform.cache import get_or_set
from sentinelai.platform.config import get_settings
from sentinelai.platform.redis import create_redis

pytestmark = pytest.mark.integration


async def test_get_or_set_only_calls_loader_on_miss() -> None:
    redis = create_redis(get_settings())
    key = "test:cache:widget"
    calls = 0

    async def loader() -> dict[str, int]:
        nonlocal calls
        calls += 1
        return {"value": 42}

    try:
        await redis.delete(key)
        first = await get_or_set(redis, key, ttl_seconds=5, loader=loader)
        second = await get_or_set(redis, key, ttl_seconds=5, loader=loader)
        assert first == second == {"value": 42}
        assert calls == 1
    finally:
        await redis.delete(key)
        await redis.aclose()
