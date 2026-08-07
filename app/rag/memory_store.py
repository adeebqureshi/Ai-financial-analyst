"""
In-memory vector store.
"""

from __future__ import annotations

from app.rag.embedding import Embedding
from app.rag.retriever import Retriever
from app.rag.vector_store import VectorStore


class MemoryVectorStore(VectorStore):

    def __init__(self) -> None:
        self._vectors: list[Embedding] = []
        self._retriever = Retriever()

    def add(
        self,
        embedding: Embedding,
    ) -> None:

        self._vectors.append(embedding)

    def search(
        self,
        query: Embedding,
        k: int = 5,
    ) -> list[Embedding]:

        results = self._retriever.search(
            query,
            self._vectors,
            k,
        )

        return [
            result.embedding
            for result in results
        ]

    def clear(self) -> None:
        self._vectors.clear()

    @property
    def size(self) -> int:
        return len(self._vectors)