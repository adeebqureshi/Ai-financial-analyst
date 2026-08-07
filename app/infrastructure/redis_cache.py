"""
Redis cache manager.
"""

from __future__ import annotations

import os

import redis


class RedisCache:

    def __init__(self) -> None:

        self.host = os.getenv(
            "REDIS_HOST",
            "localhost",
        )

        self.port = int(
            os.getenv(
                "REDIS_PORT",
                "6379",
            )
        )

        self.client = redis.Redis(
            host=self.host,
            port=self.port,
            decode_responses=True,
        )

    def ping(self) -> bool:

        try:
            return bool(
                self.client.ping()
            )
        except Exception:
            return False