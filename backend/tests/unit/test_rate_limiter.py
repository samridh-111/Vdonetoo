import pytest
import redis as redis_lib

from app.core import rate_limiter
from app.core.config import get_settings

_TEST_REDIS_URL = "redis://localhost:6379/15"  # a high-numbered DB to avoid clobbering real data


@pytest.fixture
def redis_client():
    client = redis_lib.Redis.from_url(_TEST_REDIS_URL, decode_responses=True)
    try:
        client.ping()
    except redis_lib.exceptions.ConnectionError:
        pytest.skip("No local Redis available on localhost:6379 for rate limiter test.")
    client.flushdb()
    yield client
    client.flushdb()


def test_acquire_succeeds_up_to_capacity_then_blocks(redis_client, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ELEVENLABS_MAX_CONCURRENCY", "3")
    monkeypatch.setenv("ELEVENLABS_RATE_PER_MIN", "60")
    get_settings.cache_clear()

    results = [rate_limiter.try_acquire(redis_client) for _ in range(4)]

    assert results == [True, True, True, False]


def test_refill_tops_bucket_back_up_to_capacity(redis_client, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ELEVENLABS_MAX_CONCURRENCY", "2")
    monkeypatch.setenv("ELEVENLABS_RATE_PER_MIN", "60")
    get_settings.cache_clear()

    assert rate_limiter.try_acquire(redis_client) is True
    assert rate_limiter.try_acquire(redis_client) is True
    assert rate_limiter.try_acquire(redis_client) is False

    rate_limiter.refill(redis_client)  # +1 token/sec at 60/min, capped at capacity=2

    assert rate_limiter.try_acquire(redis_client) is True
    assert rate_limiter.try_acquire(redis_client) is False
