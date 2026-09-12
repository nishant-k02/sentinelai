from __future__ import annotations

import json
from collections.abc import Awaitable, Callable

from redis.asyncio import Redis


async def get_or_set[T](
    redis: Redis,
    key: str,
    ttl_seconds: int,
    loader: Callable[[], Awaitable[T]],
) -> T:
    """Cache-aside: return the cached value at `key`, or compute it via
    `loader`, store it with a TTL, and return it.

    `loader` must be safe to call more than once — under concurrent misses on
    the same key, more than one caller can run it (a "cache stampede"). We
    accept that here; a single-flight lock is the fix if the loader is
    expensive and hot, and is not needed yet.
    """
    cached = await redis.get(key)
    if cached is not None:
        return json.loads(cached)  # type: ignore[no-any-return]

    value = await loader()
    await redis.set(key, json.dumps(value), ex=ttl_seconds)
    return value
