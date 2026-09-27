from __future__ import annotations
import os
from unittest.mock import patch
import pytest
from sqlalchemy.pool import StaticPool
from app.infrastructure.postgres import PostgreSQLManager, create_db_engine
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
        assert engine.pool.size() == 10
        engine.dispose()
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
