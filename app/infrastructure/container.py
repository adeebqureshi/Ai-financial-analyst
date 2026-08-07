"""
Dependency container.
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