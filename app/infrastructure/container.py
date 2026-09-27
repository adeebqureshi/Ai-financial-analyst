from __future__ import annotations

from app.infrastructure.postgres import PostgreSQLManager
from app.vectorstore.qdrant_store import QdrantStore


class QdrantHealthProbe:

    def __init__(self) -> None:
        self._store: QdrantStore | None = None

    def heartbeat(self) -> bool:
        try:
            if self._store is None:
                self._store = QdrantStore()
            self._store.count()
        except Exception:
            return False
        return True


class Container:

    def __init__(self) -> None:
        self.database = PostgreSQLManager()
        self.vector_store = QdrantHealthProbe()

    def health(self) -> dict[str, bool]:
        return {
            "database": self.database.health_check(),
            "vector_store": self.vector_store.heartbeat(),
            "cache": True,
        }

    def close(self) -> None:
        self.database.dispose()
