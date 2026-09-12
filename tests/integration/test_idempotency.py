import asyncio

import pytest

from sentinelai.platform.config import get_settings
from sentinelai.platform.idempotency import mark_if_new
from sentinelai.platform.redis import create_redis

pytestmark = pytest.mark.integration


async def test_second_claim_on_same_key_is_rejected() -> None:
    redis = create_redis(get_settings())
    key = "test:idempotency:event-123"
    try:
        await redis.delete(key)
        assert await mark_if_new(redis, key, ttl_seconds=5) is True
        assert await mark_if_new(redis, key, ttl_seconds=5) is False
    finally:
        await redis.delete(key)
        await redis.aclose()


async def test_concurrent_claims_have_exactly_one_winner() -> None:
    """Simulates two consumers racing on the same redelivered message:
    exactly one should be told to process it."""
    redis = create_redis(get_settings())
    key = "test:idempotency:race"
    try:
        await redis.delete(key)
        results = await asyncio.gather(
            mark_if_new(redis, key, ttl_seconds=5),
            mark_if_new(redis, key, ttl_seconds=5),
        )
        assert sorted(results) == [False, True]
    finally:
        await redis.delete(key)
        await redis.aclose()
