import asyncio
import time

import pytest
import redis as redis_lib

from app.core import rate_limiter

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


def test_acquire_succeeds_up_to_capacity_then_blocks(redis_client) -> None:
    results = [rate_limiter.try_acquire(redis_client, "test-bucket", capacity=3) for _ in range(4)]

    assert results == [True, True, True, False]


def test_refill_tops_bucket_back_up_to_capacity(redis_client) -> None:
    assert rate_limiter.try_acquire(redis_client, "test-bucket", capacity=2) is True
    assert rate_limiter.try_acquire(redis_client, "test-bucket", capacity=2) is True
    assert rate_limiter.try_acquire(redis_client, "test-bucket", capacity=2) is False

    rate_limiter.refill(redis_client, "test-bucket", capacity=2, rate_per_min=60)  # +1 token/sec

    assert rate_limiter.try_acquire(redis_client, "test-bucket", capacity=2) is True
    assert rate_limiter.try_acquire(redis_client, "test-bucket", capacity=2) is False


def test_buckets_are_independent(redis_client) -> None:
    assert rate_limiter.try_acquire(redis_client, "bucket-a", capacity=1) is True
    assert rate_limiter.try_acquire(redis_client, "bucket-a", capacity=1) is False
    # bucket-b's capacity is untouched by bucket-a's exhaustion
    assert rate_limiter.try_acquire(redis_client, "bucket-b", capacity=1) is True


async def test_wait_for_token_returns_true_once_available(redis_client) -> None:
    assert rate_limiter.try_acquire(redis_client, "wait-bucket", capacity=1) is True  # drain it

    async def refill_shortly() -> None:
        await asyncio.sleep(0.2)
        rate_limiter.refill(redis_client, "wait-bucket", capacity=1, rate_per_min=6000)  # fast refill for the test

    refill_task = asyncio.ensure_future(refill_shortly())
    start = time.monotonic()
    acquired = await rate_limiter.wait_for_token(
        redis_client, "wait-bucket", capacity=1, max_wait_seconds=2, poll_interval_seconds=0.05
    )
    await refill_task

    assert acquired is True
    assert time.monotonic() - start < 2


async def test_wait_for_token_gives_up_after_max_wait(redis_client) -> None:
    assert rate_limiter.try_acquire(redis_client, "stuck-bucket", capacity=1) is True  # drain it, never refilled

    acquired = await rate_limiter.wait_for_token(
        redis_client, "stuck-bucket", capacity=1, max_wait_seconds=0.2, poll_interval_seconds=0.05
    )

    assert acquired is False
