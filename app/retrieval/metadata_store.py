"""
metadata_store.py

Stores chunk metadata for retrieval.
"""

from __future__ import annotations

from app.retrieval.models import RetrievedChunk


class MetadataStore:

    def __init__(self) -> None:
        self._store: dict[str, RetrievedChunk] = {}

    def add(
        self,
        chunk: RetrievedChunk,
    ) -> None:

        self._store[chunk.id] = chunk

    def add_many(
        self,
        chunks: list[RetrievedChunk],
    ) -> None:

        for chunk in chunks:
            self.add(chunk)

    def get(
        self,
        chunk_id: str,
    ) -> RetrievedChunk:

        return self._store[chunk_id]

    def get_many(
        self,
        ids: list[str],
    ) -> list[RetrievedChunk]:

        return [
            self._store[i]
            for i in ids
            if i in self._store
        ]