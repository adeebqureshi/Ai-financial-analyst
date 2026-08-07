"""
rank_fusion.py

Reciprocal Rank Fusion implementation.
"""

from __future__ import annotations

from collections import defaultdict


class RankFusion:
    """
    Reciprocal Rank Fusion.

    https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf
    """

    def __init__(
        self,
        k: int = 60,
    ) -> None:

        self.k = k

    def fuse(
        self,
        *rankings: list[str],
    ) -> list[str]:
        """
        Merge multiple ranked lists using RRF.
        """

        scores = defaultdict(float)

        for ranking in rankings:

            for rank, doc_id in enumerate(ranking):

                scores[doc_id] += 1 / (
                    self.k + rank + 1
                )

        ranked = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        return [
            doc
            for doc, _ in ranked
        ]