"""
reranker.py

Cross-encoder reranker.
"""

from __future__ import annotations

from sentence_transformers import CrossEncoder


class Reranker:

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    ) -> None:

        self.model = CrossEncoder(model_name)

    def rerank(
        self,
        query: str,
        documents: list[str],
    ) -> list[tuple[str, float]]:

        pairs = [
            (query, doc)
            for doc in documents
        ]

        scores = self.model.predict(pairs)

        ranked = sorted(
            zip(documents, scores),
            key=lambda x: x[1],
            reverse=True,
        )

        return ranked