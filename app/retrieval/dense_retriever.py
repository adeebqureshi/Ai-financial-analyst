"""
dense_retriever.py

Dense vector retrieval.
"""

from __future__ import annotations

from app.vectorstore.qdrant_store import QdrantStore


class DenseRetriever:

    def __init__(self) -> None:
        self.store = QdrantStore()

    def search(
        self,
        vector: list[float],
        limit: int = 5,
    ):
        return self.store.search(
            vector=vector,
            limit=limit,
        )