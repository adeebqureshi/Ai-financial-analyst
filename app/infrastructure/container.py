"""
Dependency container.

Owns the shared infrastructure managers (primary database, Redis cache,
vector store) and their lifecycle. The container is created once per worker
process at startup and disposed on shutdown.
"""

from __future__ import annotations

from app.infrastructure.chroma import ChromaManager
from app.infrastructure.postgres import PostgreSQLManager
from app.infrastructure.redis_cache import RedisCache


class Container:

    def __init__(self) -> None:

        self.database = PostgreSQLManager()

        self.cache = RedisCache()

        self.vector_store = ChromaManager()

    def health(self) -> dict[str, bool]:
        """
        Probe each infrastructure component.

        Every check is independent: one failing component never prevents the
        others from being reported, so monitoring sees the exact failure
        surface.
        """
        return {
            "database": self.database.health_check(),
            "cache": self.cache.health_check(),
            "vector_store": self.vector_store.heartbeat(),
        }

    def close(self) -> None:
        """Dispose every managed connection (idempotent, best-effort)."""
        self.database.dispose()
        self.cache.close()