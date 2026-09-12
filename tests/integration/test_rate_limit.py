import pytest

from sentinelai.platform.config import get_settings
from sentinelai.platform.rate_limit import is_allowed
from sentinelai.platform.redis import create_redis

pytestmark = pytest.mark.integration


async def test_allows_up_to_limit_then_blocks() -> None:
    redis = create_redis(get_settings())
    key = "test:ratelimit:user-1"
    try:
        await redis.delete(key)
        results = [await is_allowed(redis, key, limit=3, window_seconds=5) for _ in range(5)]
        assert results == [True, True, True, False, False]
    finally:
        await redis.delete(key)
        await redis.aclose()
