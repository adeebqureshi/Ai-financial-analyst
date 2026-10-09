from __future__ import annotations

from app.vectorstore.qdrant_store import QdrantStore


class DenseRetriever:
    def __init__(self, store: QdrantStore | None = None) -> None:
        # A store is constructed per DenseRetriever, and a retriever per
        # request. Sharing the process-wide Qdrant client (see qdrant_store)
        # keeps this cheap; callers that already hold a store may inject it.
        self.store = store or QdrantStore()

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

    @staticmethod
    def points_to_scores(points) -> dict[str, float]:
        """Derive chunk_id -> cosine scores from already-fetched points."""
        scores: dict[str, float] = {}
        for point in points:
            payload = getattr(point, "payload", None) or {}
            chunk_id = payload.get("chunk_id") or str(point.id)
            score = getattr(point, "score", None)
            if isinstance(score, (int, float)) and not isinstance(score, bool):
                scores[chunk_id] = float(score)
        return scores

    def similarity_scores(
        self,
        vector: list[float],
        limit: int = 5,
        document_id: str | None = None,
        owner_id: str | None = None,
    ) -> dict[str, float]:
        points = self.search(
            vector=vector,
            limit=limit,
            document_id=document_id,
            owner_id=owner_id,
        )
        return self.points_to_scores(points)
