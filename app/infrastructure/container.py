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
        return {
            "database": self.database.health_check(),
            "cache": self.cache.health_check(),
            "vector_store": self.vector_store.heartbeat(),
        }
    def close(self) -> None:
        self.database.dispose()
        self.cache.close()