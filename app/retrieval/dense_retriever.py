from __future__ import annotations
from app.vectorstore.qdrant_store import QdrantStore
class DenseRetriever:
    def __init__(self) -> None:
        self.store = QdrantStore()
    def search(
        self,
        vector: list[float],
        limit: int = 5,
        document_id: str | None = None,
        owner_id: str | None = None,
    ):
        return self.store.search(
            vector=vector,
            limit=limit,
            document_id=document_id,
            owner_id=owner_id,
        )