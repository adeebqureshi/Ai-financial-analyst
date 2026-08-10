"""
qdrant_store.py

Qdrant vector database implementation.

Design Decisions:
    - **Shared in-memory client**: ``QdrantClient(":memory:")`` creates a
      fresh empty database per instance, which would silently lose data
      between requests. A module-level client is therefore shared across all
      ``QdrantStore`` instances in the process so that document vectors
      persist for the lifetime of the server.
    - **Environment-driven configuration**: When ``QDRANT_URL`` /
      ``QDRANT_API_KEY`` are set the store connects to a remote Qdrant
      server; otherwise it falls back to the shared in-memory database.
    - **Document scoping**: Every point payload carries a ``document_id``
      and searches can be restricted to a single document via a metadata
      filter, enabling "search this uploaded document" workflows.
"""

from __future__ import annotations

import os

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    FilterSelector,
    MatchValue,
    PointIdsList,
    PointStruct,
    VectorParams,
)

from app.vectorstore.base_vector_store import BaseVectorStore

_DEFAULT_COLLECTION = "financial_documents"

_DEFAULT_VECTOR_SIZE = 1536

_client: QdrantClient | None = None


def _get_shared_client(
    url: str | None,
    api_key: str | None,
) -> QdrantClient:
    """
    Return a process-wide Qdrant client.

    Remote connections create their own client; local development shares a
    single in-memory database so vectors survive across requests.
    """
    global _client

    if url:
        return QdrantClient(url=url, api_key=api_key)

    if _client is None:
        _client = QdrantClient(":memory:")

    return _client


class QdrantStore(BaseVectorStore):
    """
    Qdrant vector database.
    """

    def __init__(
        self,
        collection_name: str | None = None,
        vector_size: int | None = None,
        url: str | None = None,
        api_key: str | None = None,
    ) -> None:

        self.collection_name = (
            collection_name or os.getenv("QDRANT_COLLECTION") or _DEFAULT_COLLECTION
        )

        self.vector_size = (
            vector_size
            or int(os.getenv("EMBEDDING_DIMENSION", _DEFAULT_VECTOR_SIZE))
        )

        self.client = _get_shared_client(
            url or os.getenv("QDRANT_URL"),
            api_key or os.getenv("QDRANT_API_KEY"),
        )

        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """
        Create the collection if it does not exist; validate dimensions.
        """
        collections = {
            c.name
            for c in self.client.get_collections().collections
        }

        if self.collection_name not in collections:

            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE,
                ),
            )

            return

        info = self.client.get_collection(self.collection_name)

        stored_size = getattr(
            getattr(info.config.params, "vectors", None),
            "size",
            None,
        )

        if stored_size is not None and stored_size != self.vector_size:
            raise ValueError(
                f"Collection '{self.collection_name}' exists with vector size "
                f"{stored_size} but {self.vector_size} is required."
            )

    @staticmethod
    def _document_filter(document_id: str) -> Filter:
        return Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id),
                )
            ]
        )

    def upsert(
        self,
        ids: list[int | str],
        vectors: list[list[float]],
        payloads: list[dict],
    ) -> None:

        points = []

        for idx, vector, payload in zip(
            ids,
            vectors,
            payloads,
        ):

            points.append(
                PointStruct(
                    id=idx,
                    vector=vector,
                    payload=payload,
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

    def search(
        self,
        vector: list[float],
        limit: int = 5,
        document_id: str | None = None,
    ):

        query_filter = (
            self._document_filter(document_id)
            if document_id
            else None
        )

        return self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            limit=limit,
            query_filter=query_filter,
        ).points

    def delete(
        self,
        ids: list[int | str],
    ) -> None:

        self.client.delete(
            collection_name=self.collection_name,
            points_selector=PointIdsList(points=list(ids)),
        )

    def delete_by_document_id(
        self,
        document_id: str,
    ) -> None:

        self.client.delete(
            collection_name=self.collection_name,
            points_selector=FilterSelector(
                filter=self._document_filter(document_id),
            ),
        )

    def get_all(
        self,
        limit: int = 10_000,
    ):
        """
        Return every point in the collection (used to rebuild BM25 indexes).
        """
        points, _ = self.client.scroll(
            collection_name=self.collection_name,
            limit=limit,
        )

        return points

    def count(self) -> int:
        return self.client.count(
            collection_name=self.collection_name,
        ).count
