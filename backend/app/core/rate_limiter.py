"""Redis-backed token bucket rate limiter, generalized across named buckets
(currently "elevenlabs" and "translation").

Authoritative across every worker process/machine (unlike Celery's own
per-worker `rate_limit=`), so a batch of 50 rows and a batch of 1000 rows
both respect the same global throughput ceiling for a given external API --
larger batches just deepen the queue instead of widening concurrency.

Each bucket is refilled by a celery-beat task (see core/celery_app.py's
beat_schedule) at a rate derived from that bucket's *_RATE_PER_MIN setting.
"""

import asyncio

from redis import Redis

_KEY_PREFIX = "rate_limiter:tokens:"

_ACQUIRE_SCRIPT = """
local tokens = tonumber(redis.call('GET', KEYS[1]))
if tokens == nil then
  tokens = tonumber(ARGV[1])
  redis.call('SET', KEYS[1], tokens)
end
if tokens >= 1 then
  redis.call('DECRBY', KEYS[1], 1)
  return 1
end
return 0
"""

_REFILL_SCRIPT = """
local current = tonumber(redis.call('GET', KEYS[1]) or ARGV[1])
local capacity = tonumber(ARGV[1])
local increment = tonumber(ARGV[2])
local updated = math.min(capacity, current + increment)
redis.call('SET', KEYS[1], updated)
return updated
"""


def try_acquire(redis_client: Redis, bucket: str, capacity: int) -> bool:
    """Attempt to take one token from the named bucket. Returns False if the
    bucket is empty -- caller should retry with backoff, not fail the job."""
    result = redis_client.eval(_ACQUIRE_SCRIPT, 1, f"{_KEY_PREFIX}{bucket}", str(capacity))
    return bool(result)


def refill(redis_client: Redis, bucket: str, capacity: int, rate_per_min: float) -> None:
    """Called once per second by celery-beat to top the named bucket back up."""
    increment_per_tick = rate_per_min / 60.0
    redis_client.eval(
        _REFILL_SCRIPT,
        1,
        f"{_KEY_PREFIX}{bucket}",
        str(capacity),
        str(increment_per_tick),
    )


async def wait_for_token(
    redis_client: Redis,
    bucket: str,
    capacity: int,
    *,
    max_wait_seconds: float = 60.0,
    poll_interval_seconds: float = 0.5,
) -> bool:
    """Used from plain async code (not a Celery task's own self.retry loop)
    that needs to throttle itself against a bucket -- e.g. prepare_script's
    translation calls. Returns False (instead of waiting forever) if the
    bucket is still empty after max_wait_seconds, so a stuck bucket can't
    wedge the whole pipeline; the caller proceeds and lets the provider's own
    retry/backoff handle it from there."""
    elapsed = 0.0
    while elapsed < max_wait_seconds:
        if try_acquire(redis_client, bucket, capacity):
            return True
        await asyncio.sleep(poll_interval_seconds)
        elapsed += poll_interval_seconds
    return False
