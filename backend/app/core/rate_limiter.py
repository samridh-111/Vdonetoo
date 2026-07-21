"""Redis-backed token bucket rate limiter for ElevenLabs calls.

Authoritative across every worker process/machine (unlike Celery's own
per-worker `rate_limit=`), so a batch of 50 rows and a batch of 1000 rows
both respect the same global ElevenLabs throughput ceiling -- larger batches
just deepen the queue instead of widening concurrency.

Bucket capacity = ELEVENLABS_MAX_CONCURRENCY. Refilled by a celery-beat task
(`refill_rate_limit_tokens`, scheduled every second in celery_app.py) at a
rate derived from ELEVENLABS_RATE_PER_MIN.
"""

from redis import Redis

from app.core.config import get_settings

_TOKENS_KEY = "elevenlabs:rate_limiter:tokens"

_ACQUIRE_SCRIPT = """
local tokens = tonumber(redis.call('GET', KEYS[1]) or ARGV[1])
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


def try_acquire(redis_client: Redis) -> bool:
    """Attempt to take one token from the bucket. Returns False if the
    bucket is empty -- caller should retry with backoff, not fail the job."""
    settings = get_settings()
    result = redis_client.eval(_ACQUIRE_SCRIPT, 1, _TOKENS_KEY, str(settings.elevenlabs_max_concurrency))
    return bool(result)


def refill(redis_client: Redis) -> None:
    """Called once per second by celery-beat to top the bucket back up."""
    settings = get_settings()
    increment_per_tick = settings.elevenlabs_rate_per_min / 60.0
    redis_client.eval(
        _REFILL_SCRIPT,
        1,
        _TOKENS_KEY,
        str(settings.elevenlabs_max_concurrency),
        str(increment_per_tick),
    )
