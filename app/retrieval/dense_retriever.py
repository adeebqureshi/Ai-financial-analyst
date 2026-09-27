from __future__ import annotations

from app.vectorstore.qdrant_store import QdrantStore


class DenseRetriever:
    def __init__(self) -> None:
        self.store = QdrantStore()

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
        scores: dict[str, float] = {}
        for point in points:
            payload = getattr(point, "payload", None) or {}
            chunk_id = payload.get("chunk_id") or str(point.id)
            score = getattr(point, "score", None)
            if isinstance(score, (int, float)) and not isinstance(score, bool):
                scores[chunk_id] = float(score)
        return scores
