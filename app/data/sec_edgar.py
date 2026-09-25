from __future__ import annotations

import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)


class SECRateLimiter:
    """
    Distributed Redis-backed token bucket for SEC EDGAR requests.

    The limiter is shared across all application workers/processes through
    Redis.

    Capacity:
        10 requests

    Refill rate:
        10 requests per second

    Behavior:
        - Allows an initial burst of up to 10 requests.
        - Refills at 10 tokens per second.
        - Blocks until a token is available.
        - Fails closed if Redis is unavailable.
    """

    CAPACITY = 10
    REFILL_RATE = 10.0

    DEFAULT_REDIS_URL = "redis://localhost:6379/0"
    DEFAULT_KEY = "sec:edgar:token_bucket"

    _SCRIPT = """
    local key = KEYS[1]

    local capacity = tonumber(ARGV[1])
    local refill_rate = tonumber(ARGV[2])

    -- Use Redis server time so all workers share the same clock.
    local redis_time = redis.call("TIME")
    local now = tonumber(redis_time[1])
        + (tonumber(redis_time[2]) / 1000000)

    -- Read current bucket state.
    local values = redis.call(
        "HMGET",
        key,
        "tokens",
        "timestamp"
    )

    local tokens = tonumber(values[1])
    local timestamp = tonumber(values[2])

    -- Initialize a new bucket at full capacity.
    if tokens == nil or timestamp == nil then
        tokens = capacity
        timestamp = now
    end

    -- Calculate tokens accumulated since the previous request.
    local elapsed = math.max(0, now - timestamp)

    tokens = math.min(
        capacity,
        tokens + (elapsed * refill_rate)
    )

    -- Consume one token if available.
    if tokens >= 1 then
        tokens = tokens - 1

        redis.call(
            "HSET",
            key,
            "tokens",
            tokens,
            "timestamp",
            now
        )

        -- Automatically clean up an inactive bucket.
        redis.call("EXPIRE", key, 60)

        return {1, 0}
    end

    -- No token is currently available.
    -- Calculate how long until one token exists.
    local wait_time = (1 - tokens) / refill_rate

    redis.call(
        "HSET",
        key,
        "tokens",
        tokens,
        "timestamp",
        now
    )

    redis.call("EXPIRE", key, 60)

    return {0, wait_time}
    """

    def __init__(
        self,
        redis_url: str | None = None,
        key: str = DEFAULT_KEY,
    ) -> None:
        try:
            import redis
        except ImportError as exc:
            raise RuntimeError(
                "The 'redis' Python package is required for SEC rate limiting."
            ) from exc

        self._redis_url = (
            redis_url
            or os.getenv("REDIS_URL")
            or self.DEFAULT_REDIS_URL
        )

        self._key = key

        self._client: Any = redis.from_url(
            self._redis_url,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
            health_check_interval=30,
        )

        # Fail closed. If Redis cannot be reached, we must not make
        # an unthrottled SEC request.
        try:
            self._client.ping()
        except Exception as exc:
            logger.error(
                "SEC Redis rate limiter is unavailable: %s",
                exc,
            )
            raise RuntimeError(
                "Redis is required for SEC EDGAR rate limiting, "
                "but the Redis server is unavailable."
            ) from exc

        logger.info(
            "SEC EDGAR Redis token bucket initialized "
            "(capacity=%d, refill_rate=%.1f/sec)",
            self.CAPACITY,
            self.REFILL_RATE,
        )

    def acquire(self) -> None:
        """
        Acquire one SEC request token.

        Blocks until a token becomes available.

        Raises:
            RuntimeError:
                If Redis becomes unavailable while acquiring a token.

        Important:
            This method must be called immediately before every operation
            that can make a request to SEC EDGAR.
        """

        while True:
            try:
                result = self._client.eval(
                    self._SCRIPT,
                    1,
                    self._key,
                    self.CAPACITY,
                    self.REFILL_RATE,
                )
            except Exception as exc:
                logger.error(
                    "SEC Redis rate limiter failed: %s",
                    exc,
                )

                # Fail closed. Never bypass SEC rate limiting.
                raise RuntimeError(
                    "SEC EDGAR request blocked because the Redis "
                    "rate limiter is unavailable."
                ) from exc

            if not result or len(result) < 2:
                raise RuntimeError(
                    "SEC Redis rate limiter returned an invalid response."
                )

            allowed = int(result[0])
            wait_time = float(result[1])

            if allowed == 1:
                return

            # Sleep only for the amount of time calculated atomically
            # by Redis. A minimum prevents a busy loop from occurring
            # because of floating-point precision.
            time.sleep(max(wait_time, 0.001))