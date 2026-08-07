"""
Simple reranker.
"""

from __future__ import annotations

from app.rag.cross_encoder import CrossEncoder
from app.rag.search_result import SearchResult


class RuleBasedCrossEncoder(CrossEncoder):
    """
    Lightweight reranker used for testing.
    """

    def score(
        self,
        query: str,
        document: str,
    ) -> float:

        query_words = {
            word.lower()
            for word in query.split()
        }

        document_words = {
            word.lower()
            for word in document.split()
        }

        overlap = len(
            query_words & document_words
        )

        return float(overlap)


class Reranker:

    def __init__(
        self,
        encoder: CrossEncoder | None = None,
    ) -> None:

        self.encoder = encoder or RuleBasedCrossEncoder()

    def rerank(
        self,
        query: str,
        results: list[SearchResult],
    ) -> list[SearchResult]:

        rescored = []

        for result in results:

            rescored.append(
                SearchResult(
                    embedding=result.embedding,
                    score=self.encoder.score(
                        query,
                        result.embedding.text,
                    ),
                )
            )

        rescored.sort(
            key=lambda result: result.score,
            reverse=True,
        )

        return rescored