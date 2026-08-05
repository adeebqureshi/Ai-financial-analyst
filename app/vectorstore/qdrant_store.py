"""
qdrant_store.py

Qdrant vector database implementation.
"""

from __future__ import annotations

from qdrant_client import QdrantClient
from qdrant_client.models import Distance
from qdrant_client.models import PointStruct
from qdrant_client.models import VectorParams

from app.vectorstore.base_vector_store import BaseVectorStore


class QdrantStore(BaseVectorStore):
    """
    Qdrant vector database.
    """

    def __init__(
        self,
        collection_name: str = "financial_documents",
        vector_size: int = 1536,
    ) -> None:

        self.collection_name = collection_name

        self.client = QdrantClient(":memory:")

        collections = [
            c.name
            for c in self.client.get_collections().collections
        ]

        if collection_name not in collections:

            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE,
                ),
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
    ):

        return self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            limit=limit,
        ).points