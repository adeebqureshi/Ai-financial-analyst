"""
Simple document index.
"""

from __future__ import annotations

from app.rag.embedding import Embedding


class DocumentIndex:

    def __init__(self) -> None:
        self._documents: list[Embedding] = []

    def add(
        self,
        embedding: Embedding,
    ) -> None:

        self._documents.append(embedding)

    def all(self) -> list[Embedding]:
        return list(self._documents)

    def clear(self) -> None:
        self._documents.clear()

    @property
    def size(self) -> int:
        return len(self._documents)