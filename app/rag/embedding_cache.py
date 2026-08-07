"""
Simple in-memory embedding cache.
"""

from __future__ import annotations

from app.rag.embedding import Embedding


class EmbeddingCache:

    def __init__(self) -> None:
        self._cache: dict[str, Embedding] = {}

    def put(
        self,
        embedding: Embedding,
    ) -> None:

        self._cache[embedding.text] = embedding

    def get(
        self,
        text: str,
    ) -> Embedding | None:

        return self._cache.get(text)

    def clear(self) -> None:
        self._cache.clear()

    @property
    def size(self) -> int:
        return len(self._cache)