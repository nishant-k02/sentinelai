from __future__ import annotations

from redis.asyncio import Redis


async def is_allowed(redis: Redis, key: str, limit: int, window_seconds: int) -> bool:
    """Fixed-window rate limiter: at most `limit` calls per `window_seconds`
    for a given key (e.g. ``f"ratelimit:{user_id}"``).

    `INCR` is atomic, so concurrent callers each get a distinct count with no
    race. The expiry is set only on the first increment of a window (count
    == 1), giving the window a fixed start rather than resetting on every
    call (that would make it a sliding window).

    Trade-off: a client can use up to `limit` calls right at the end of one
    window and another `limit` right at the start of the next — up to ~2x
    `limit` in a short burst. A sliding-window-log or token-bucket algorithm
    avoids that at the cost of more state per key. Fixed-window is the right
    starting choice: one counter, one TTL, easy to reason about.
    """
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, window_seconds)
    return count <= limit
