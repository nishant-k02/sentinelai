from __future__ import annotations

from redis.asyncio import Redis


async def mark_if_new(redis: Redis, key: str, ttl_seconds: int) -> bool:
    """Atomically claim `key` as processed.

    Returns True the first time a given key is seen - the caller should
    proceed. Returns False if it was already claimed - the caller should
    skip; this is a duplicate delivery.

    `SET key value NX EX ttl` is one atomic Redis command: "set only if it
    doesn't already exist, with an expiry." A naive `GET` then `SET` from
    Python has a race window between the two calls where two callers can
    both see "not present" and both proceed — this doesn't.
    """
    was_set = await redis.set(key, "1", nx=True, ex=ttl_seconds)
    return bool(was_set)
