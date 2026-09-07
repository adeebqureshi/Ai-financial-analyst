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

        # Parallel owner list so sparse (BM25) results can be tenant-scoped
        # before rank fusion. ``None`` entries mean "legacy / unowned".
        self.owner_ids: list[str | None] = []

        self.index: BM25Okapi | None = None

    def build(
        self,
        ids: list[str],
        documents: list[str],
        owner_ids: list[str | None] | None = None,
    ) -> None:
        """
        Build BM25 index.
        """

        if len(ids) != len(documents):
            raise ValueError(
                "ids and documents must have the same length."
            )

        if owner_ids is not None and len(owner_ids) != len(ids):
            raise ValueError(
                "owner_ids must have the same length as ids."
            )

        self.ids = ids

        self.documents = documents

        self.owner_ids = list(owner_ids) if owner_ids is not None else [
            None
        ] * len(ids)

        if not documents:
            self.index = None

            return

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
        owner_id: str | None = None,
    ) -> list[str]:
        """
        Return ranked document IDs.

        If the index has not been built yet (no documents ingested), an
        empty list is returned so callers degrade gracefully instead of
        crashing with a runtime error.

        When ``owner_id`` is provided, only chunks owned by that user are
        returned. Filtering happens BEFORE the top-k truncation so that
        chunks belonging to other tenants can never displace the caller's
        own chunks from the sparse candidate list (tenant isolation).
        """
        if self.index is None:
            return []

        tokens = query.lower().split()

        scores = self.index.get_scores(tokens)

        ranked = sorted(
            zip(
                scores,
                self.ids,
                self.owner_ids,
            ),
            reverse=True,
        )

        results: list[str] = []

        for _score, doc_id, doc_owner in ranked:
            if owner_id is not None and doc_owner != owner_id:
                continue

            results.append(doc_id)

            if len(results) >= top_k:
                break

        return results