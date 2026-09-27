from __future__ import annotations

from app.infrastructure.postgres import PostgreSQLManager
from app.vectorstore.qdrant_store import QdrantStore


class QdrantHealthProbe:
    """Health probe for the single vector database (Qdrant).

    Replaces the former ChromaDB probe. Chroma was a second, unused vector
    database that only answered a heartbeat in the health container; Qdrant is
    the vector store the RAG pipeline actually reads and writes.
    """

    def __init__(self) -> None:
        self._store: QdrantStore | None = None

    def heartbeat(self) -> bool:
        """Return True when the Qdrant collection is reachable.

        Qdrant is configured either as a local ``:memory:`` client (default) or
        against a server via QDRANT_URL, so a successful ``count()`` proves the
        collection exists and is queryable.
        """
        try:
            if self._store is None:
                self._store = QdrantStore()
            self._store.count()
        except Exception:
            return False
        return True


class Container:
    """Infrastructure health container for the readiness probe.

    There is no separate cache service: quote and chat caches are in-process,
    so nothing external needs to be probed.
    """

    def __init__(self) -> None:
        self.database = PostgreSQLManager()
        self.vector_store = QdrantHealthProbe()

    def health(self) -> dict[str, bool]:
        return {
            "database": self.database.health_check(),
            "vector_store": self.vector_store.heartbeat(),
            # No external cache service exists; reported for response shape.
            "cache": True,
        }

    def close(self) -> None:
        self.database.dispose()