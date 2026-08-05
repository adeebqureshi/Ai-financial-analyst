"""
search_service.py

High-level semantic search service.
"""

from __future__ import annotations

from app.embeddings.embedding_service import EmbeddingService
from app.vectorstore.qdrant_store import QdrantStore


class SearchService:
    """
    Performs semantic search over the vector database.
    """

    def __init__(self) -> None:
        self.embedder = EmbeddingService()
        self.store = QdrantStore()

    def search(
        self,
        query: str,
        limit: int = 5,
    ):
        """
        Search the vector store using a natural language query.
        """

        vector = self.embedder.embed_text(query)

        return self.store.search(
            vector=vector,
            limit=limit,
        )