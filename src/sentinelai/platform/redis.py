from __future__ import annotations

from redis.asyncio import Redis

from sentinelai.platform.config import Settings


def create_redis(settings: Settings) -> Redis:
    """Create the async Redis client (backed by an internal connection pool).

    One client per process. ``decode_responses=True`` makes it return ``str``
    instead of ``bytes`` — convenient now; revisit if we store binary blobs.
    """
    return Redis.from_url(settings.redis_url, decode_responses=True)
