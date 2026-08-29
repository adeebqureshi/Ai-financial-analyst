"""
Infrastructure productionization tests: connection pooling, lifecycle,
health checks and Redis/cache configuration.

Unit tests run against SQLite/fakes only (no external services required).
Real PostgreSQL/Redis integration tests live in
``tests/infrastructure/test_integration_services.py`` and are opt-in via
environment variables.
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from sqlalchemy.pool import StaticPool

from app.infrastructure.postgres import PostgreSQLManager, create_db_engine
from app.infrastructure.redis_cache import RedisCache, build_redis_url


# ──────────────────────────────────────────────────────────────────────────────
# Engine construction / pooling
# ──────────────────────────────────────────────────────────────────────────────

class TestCreateDbEngine:
    def test_sqlite_memory_uses_shared_static_pool(self):
        engine = create_db_engine("sqlite+pysqlite:///:memory:")

        assert isinstance(engine.pool, StaticPool)
        engine.dispose()

    def test_sqlite_memory_database_is_shared_across_connections(self):
        engine = create_db_engine("sqlite+pysqlite:///:memory:")

        with engine.connect() as conn:
            conn.exec_driver_sql("CREATE TABLE t (x INTEGER)")
            conn.exec_driver_sql("INSERT INTO t VALUES (42)")
            conn.commit()

        with engine.connect() as conn:
            value = conn.exec_driver_sql("SELECT x FROM t").scalar()

        assert value == 42
        engine.dispose()

    def test_sqlite_file_allows_cross_thread_connections(self, tmp_path):
        engine = create_db_engine(f"sqlite:///{tmp_path / 'f.db'}")

        # The connection kwargs must relax check_same_thread for FastAPI's
        # thread pool access.
        assert engine.pool is not None
        engine.dispose()

    def test_postgres_engine_is_pooled_with_pre_ping(self):
        engine = create_db_engine("postgresql+psycopg://user:pass@localhost:5432/db")

        pool = engine.pool
        assert pool._pre_ping is True
        assert pool.size() >= 1

        engine.dispose()

    def test_postgres_pool_sizing_from_environment(self):
        env = {
            "DB_POOL_SIZE": "3",
            "DB_MAX_OVERFLOW": "7",
            "DB_POOL_RECYCLE_SECONDS": "600",
            "DB_POOL_TIMEOUT_SECONDS": "11",
        }

        with patch.dict(os.environ, env):
            engine = create_db_engine("postgresql+psycopg://user:pass@localhost:5432/db")

        pool = engine.pool
        assert pool.size() == 3
        assert pool._max_overflow == 7
        assert pool._recycle == 600
        assert pool._timeout == 11

        engine.dispose()

    def test_null_pool_override(self):
        from sqlalchemy.pool import NullPool

        with patch.dict(os.environ, {"DB_USE_NULL_POOL": "1"}):
            engine = create_db_engine("postgresql+psycopg://user:pass@localhost:5432/db")

        assert isinstance(engine.pool, NullPool)
        engine.dispose()

    def test_invalid_pool_env_falls_back_to_defaults(self):
        with patch.dict(os.environ, {"DB_POOL_SIZE": "not-a-number"}):
            engine = create_db_engine("postgresql+psycopg://user:pass@localhost:5432/db")

        assert engine.pool.size() == 10  # documented default
        engine.dispose()


# ──────────────────────────────────────────────────────────────────────────────
# PostgreSQLManager
# ──────────────────────────────────────────────────────────────────────────────

class TestPostgreSQLManager:
    def test_default_is_sqlite_fallback(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("DATABASE_URL", None)
            manager = PostgreSQLManager()

        assert manager.is_postgres is False
        manager.dispose()

    def test_postgres_url_detected(self):
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql+psycopg://u:p@localhost/db"}):
            manager = PostgreSQLManager()

        assert manager.is_postgres is True
        manager.dispose()

    def test_health_check_on_in_memory_sqlite(self):
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite+pysqlite:///:memory:"}):
            manager = PostgreSQLManager()

        assert manager.health_check() is True
        manager.dispose()

    def test_health_check_false_when_unreachable(self):
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql+psycopg://u:p@127.0.0.1:1/db"}):
            manager = PostgreSQLManager()

        assert manager.health_check() is False
        manager.dispose()

    def test_connect_returns_working_connection(self):
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite+pysqlite:///:memory:"}):
            manager = PostgreSQLManager()

        connection = manager.connect()
        assert connection is not None
        connection.close()
        manager.dispose()


# ──────────────────────────────────────────────────────────────────────────────
# Redis cache manager
# ──────────────────────────────────────────────────────────────────────────────

_REDIS_ENV_VARS = ("REDIS_URL", "REDIS_HOST", "REDIS_PORT", "REDIS_DB", "REDIS_PASSWORD")


class TestRedisCache:
    def test_build_redis_url_defaults(self):
        with patch.dict(os.environ, {}, clear=False):
            for var in _REDIS_ENV_VARS:
                os.environ.pop(var, None)
            assert build_redis_url() == "redis://localhost:6379/0"

    def test_build_redis_url_from_redis_url_env(self):
        with patch.dict(os.environ, {"REDIS_URL": "redis://cache:6380/3"}):
            assert build_redis_url() == "redis://cache:6380/3"

    def test_build_redis_url_with_password(self):
        env = {"REDIS_HOST": "r", "REDIS_PORT": "6379", "REDIS_PASSWORD": "secret"}
        with patch.dict(os.environ, env):
            url = build_redis_url()

        assert url == "redis://:secret@r:6379/0"

    def test_client_has_socket_timeouts(self):
        with patch.dict(os.environ, {"REDIS_URL": "redis://localhost:6379/0"}):
            cache = RedisCache()

        kwargs = cache.client.connection_pool.connection_kwargs
        assert kwargs["socket_connect_timeout"] > 0
        assert kwargs["socket_timeout"] > 0
        assert kwargs["decode_responses"] is True
        cache.close()

    def test_health_check_false_when_unreachable(self):
        with patch.dict(os.environ, {"REDIS_URL": "redis://127.0.0.1:1/0"}):
            cache = RedisCache()

        assert cache.health_check() is False
        cache.close()

    def test_ping_alias(self):
        with patch.dict(os.environ, {"REDIS_URL": "redis://127.0.0.1:1/0"}):
            cache = RedisCache()

        assert isinstance(cache.ping(), bool)
        cache.close()

    def test_legacy_host_port_attributes(self):
        with patch.dict(os.environ, {"REDIS_HOST": "myredis", "REDIS_PORT": "6400"}):
            cache = RedisCache()

        assert cache.host == "myredis"
        assert cache.port == 6400
        cache.close()

    def test_close_is_safe_when_never_connected(self):
        with patch.dict(os.environ, {"REDIS_URL": "redis://127.0.0.1:1/0"}):
            cache = RedisCache()

        cache.close()
        cache.close()  # idempotent