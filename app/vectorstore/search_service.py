from __future__ import annotations
from app.embeddings.embedding_service import EmbeddingService
from app.vectorstore.qdrant_store import QdrantStore
class SearchService:
    def __init__(self) -> None:
        self.embedder = EmbeddingService()
        self.store = QdrantStore()
    def search(
        self,
        query: str,
        limit: int = 5,
    ):
        vector = self.embedder.embed_text(query)
        return self.store.search(
            vector=vector,
            limit=limit,
        )