"""
bm25_index.py

Sparse keyword retrieval using BM25.
"""

from __future__ import annotations

from rank_bm25 import BM25Okapi


class BM25Index:
    """
    BM25 keyword retrieval.
    """

    def __init__(self) -> None:

        self.ids: list[str] = []

        self.documents: list[str] = []

        self.index: BM25Okapi | None = None

    def build(
        self,
        ids: list[str],
        documents: list[str],
    ) -> None:
        """
        Build BM25 index.
        """

        if len(ids) != len(documents):
            raise ValueError(
                "ids and documents must have the same length."
            )

        self.ids = ids

        self.documents = documents

        tokenized = [
            doc.lower().split()
            for doc in documents
        ]

        self.index = BM25Okapi(
            tokenized,
        )

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[str]:
        """
        Return ranked document IDs.
        """

        if self.index is None:
            raise RuntimeError(
                "BM25 index has not been built."
            )

        tokens = query.lower().split()

        scores = self.index.get_scores(tokens)

        ranked = sorted(
            zip(
                scores,
                self.ids,
            ),
            reverse=True,
        )

        return [
            doc_id
            for _, doc_id in ranked[:top_k]
        ]