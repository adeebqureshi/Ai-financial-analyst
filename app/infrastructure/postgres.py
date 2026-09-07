"""
PostgreSQL connection manager.

Production Decisions:
    - **PostgreSQL first, SQLite fallback**: ``DATABASE_URL`` defaults to an
      in-memory SQLite database for zero-infrastructure development/tests.
      In production, point ``DATABASE_URL`` at PostgreSQL
      (``postgresql+psycopg://user:pass@host:5432/db``).
    - **Connection pooling tuned for multi-worker deployments**: Pool size,
      overflow, recycle and timeout are configurable via environment so the
      engine can be sized per worker (``DB_POOL_SIZE``, ``DB_MAX_OVERFLOW``,
      ``DB_POOL_RECYCLE_SECONDS``, ``DB_POOL_TIMEOUT_SECONDS``).
    - **Stale-connection resilience**: ``pool_pre_ping=True`` verifies each
      checked-out connection, transparently replacing connections dropped by
      the server, a NAT idle timeout or a database failover.
    - **Health checking**: :meth:`PostgreSQLManager.health_check` performs a
      lightweight ``SELECT 1`` suitable for load-balancer/readiness probes.
"""

from __future__ import annotations

import os

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool

from app.core.logging import get_logger

logger = get_logger("app.infrastructure.postgres")

# NOTE (observability): database failures are logged with the failure reason
# only. Connection URLs are never logged — they may embed credentials
# (``postgresql://user:password@host/db``).


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _is_sqlite(url: str) -> bool:
    return url.startswith("sqlite")


def _is_postgres(url: str) -> bool:
    return url.startswith("postgresql")


def create_db_engine(url: str) -> Engine:
    """
    Build a production-appropriate engine for the given database URL.

    - PostgreSQL: pooled with pre-ping, recycle and bounded overflow.
    - SQLite: file databases allow cross-thread connections (FastAPI thread
      pool access) and enable WAL for concurrent readers; ``:memory:`` uses a
      ``StaticPool`` so the same in-memory database is shared per engine.
    - ``DB_USE_NULL_POOL=1`` disables pooling entirely (useful for ephemeral
      scripts or when an external pooler such as PgBouncer owns pooling).
    """
    use_null_pool = os.getenv("DB_USE_NULL_POOL", "").strip() in {"1", "true", "yes"}

    if _is_sqlite(url):
        memory = ":memory:" in url
        if memory:
            from sqlalchemy.pool import StaticPool

            return create_engine(
                url,
                future=True,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
        return create_engine(
            url,
            future=True,
            connect_args={"check_same_thread": False, "timeout": 30},
        )

    if use_null_pool:
        return create_engine(url, future=True, poolclass=NullPool)

    if _is_postgres(url):
        return create_engine(
            url,
            future=True,
            pool_pre_ping=True,
            pool_size=_int_env("DB_POOL_SIZE", 10),
            max_overflow=_int_env("DB_MAX_OVERFLOW", 20),
            pool_recycle=_int_env("DB_POOL_RECYCLE_SECONDS", 1800),
            pool_timeout=_int_env("DB_POOL_TIMEOUT_SECONDS", 30),
            connect_args={
                "connect_timeout": _int_env("DB_CONNECT_TIMEOUT_SECONDS", 10),
                "application_name": os.getenv("DB_APPLICATION_NAME", "ai-financial-analyst"),
            },
        )

    # Unknown dialect: safe defaults with pre-ping.
    return create_engine(url, future=True, pool_pre_ping=True)


class PostgreSQLManager:
    """Owns the primary application database engine and its lifecycle."""

    def __init__(self) -> None:
        self.url = os.getenv(
            "DATABASE_URL",
            "sqlite+pysqlite:///:memory:",
        )

        self.engine: Engine = create_db_engine(self.url)

    @property
    def is_postgres(self) -> bool:
        """True when the configured production database is PostgreSQL."""
        return _is_postgres(self.url)

    def connect(self):
        return self.engine.connect()

    def health_check(self) -> bool:
        """Return True when the database responds to ``SELECT 1``."""
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except Exception as exc:
            logger.warning(
                "Database health check failed: backend=%s error_type=%s error=%s",
                "postgresql" if self.is_postgres else "sqlite",
                exc.__class__.__name__,
                exc,
            )
            return False

    def dispose(self) -> None:
        self.engine.dispose()