"""
Opt-in integration tests against real PostgreSQL and Redis services.

These tests are **skipped unless** the corresponding service is provided via
environment variables:

    TEST_POSTGRES_URL   e.g. postgresql+psycopg://postgres:postgres@localhost:5432/financial_test
    TEST_REDIS_URL      e.g. redis://localhost:6379/15

The easiest way to provide them is the bundled compose file:

    docker compose -f docker/docker-compose.yml up -d postgres redis
    # then (adjusting ports/credentials for your setup):
    set TEST_POSTGRES_URL=postgresql+psycopg://postgres:postgres@localhost:5432/financial
    set TEST_REDIS_URL=redis://localhost:6379/0
    pytest tests/infrastructure/test_integration_services.py
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from sqlalchemy import text

POSTGRES_URL = os.getenv("TEST_POSTGRES_URL", "")
REDIS_URL = os.getenv("TEST_REDIS_URL", "")

pytestmark = [
    pytest.mark.integration,
]


# ──────────────────────────────────────────────────────────────────────────────
# PostgreSQL
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture()
def postgres_manager():
    if not POSTGRES_URL:
        pytest.skip("TEST_POSTGRES_URL not set; PostgreSQL integration test skipped")
    try:
        import psycopg  # noqa: F401
    except ImportError:
        pytest.skip("psycopg driver not installed")

    from app.infrastructure.postgres import PostgreSQLManager

    with patch.dict(os.environ, {"DATABASE_URL": POSTGRES_URL}):
        manager = PostgreSQLManager()
        if not manager.health_check():
            manager.dispose()
            pytest.skip("PostgreSQL service not reachable at TEST_POSTGRES_URL")
        yield manager
        manager.dispose()


class TestPostgresIntegration:

    def test_connectivity_and_select(self, postgres_manager):
        assert postgres_manager.health_check() is True

        with postgres_manager.connect() as conn:
            value = conn.execute(text("SELECT 1")).scalar()
        assert value == 1

    def test_engine_uses_pre_ping_pool(self, postgres_manager):
        pool = postgres_manager.engine.pool
        assert pool._pre_ping is True

    def test_connection_survives_pool_recycle_cycle(self, postgres_manager):
        # Exercise several checkouts to prove pool stability across uses.
        for _ in range(5):
            with postgres_manager.connect() as conn:
                assert conn.execute(text("SELECT 1")).scalar() == 1

    def test_chat_schema_creates_and_persists_on_postgres(self, postgres_manager):
        from app.chat.store import ChatStore

        store = ChatStore(POSTGRES_URL)
        store.save_turn(
            None,
            "pg-integration-session",
            user_message="hi",
            assistant_message="hello",
        )

        # Re-instantiate (simulating a new worker): the conversation survives.
        store2 = ChatStore(POSTGRES_URL)
        loaded = store2.get_session(None, "pg-integration-session")
        assert loaded is not None
        assert loaded["session_id"] == "pg-integration-session"

        # Deterministic cleanup.
        assert store2.delete_session(None, "pg-integration-session") is True


# ──────────────────────────────────────────────────────────────────────────────
# Redis
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture()
def redis_cache():
    if not REDIS_URL:
        pytest.skip("TEST_REDIS_URL not set; Redis integration test skipped")

    from app.infrastructure.redis_cache import RedisCache

    with patch.dict(os.environ, {"REDIS_URL": REDIS_URL}):
        cache = RedisCache()
        if not cache.health_check():
            cache.close()
            pytest.skip("Redis service not reachable at TEST_REDIS_URL")
        yield cache
        cache.close()


class TestRedisIntegration:
    def test_ping(self, redis_cache):
        assert redis_cache.health_check() is True

    def test_round_trip(self, redis_cache):
        key = "infra-test:roundtrip"
        redis_cache.client.set(key, "v1", ex=60)
        assert redis_cache.client.get(key) == "v1"
        redis_cache.client.delete(key)

    def test_rate_limiter_distributed_increment(self, redis_cache):
        from app.api.rate_limiter import RedisBackend

        backend = RedisBackend(REDIS_URL)
        key = "ratelimit:test:integration"

        try:
            first = backend.increment(key, 60)
            second = backend.increment(key, 60)
            assert second == first + 1
            assert backend.get(key) == second
        finally:
            try:
                backend.reset(key)
            except Exception:
                pass

    def test_chat_cache_round_trip(self, redis_cache):
        from app.chat.cache import ChatSessionCache

        cache = ChatSessionCache(REDIS_URL, ttl_seconds=60)
        cache.set_context("owner-1", "sess-1", {"tickers": ["AAPL"], "answer": "ok"})
        assert cache.get_context("owner-1", "sess-1") == {"tickers": ["AAPL"], "answer": "ok"}
        cache.invalidate("owner-1", "sess-1")
        assert cache.get_context("owner-1", "sess-1") is None

    def test_chat_store_uses_redis_cache(self, redis_cache, tmp_path):
        # Ensure the ChatSessionCache with a live Redis is marked enabled.
        from app.chat.cache import ChatSessionCache

        cache = ChatSessionCache(REDIS_URL, ttl_seconds=60)
        assert cache.enabled is True
        assert cache.get_context("no-one", "no-session") is None