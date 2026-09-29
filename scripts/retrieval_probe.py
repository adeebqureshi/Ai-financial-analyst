"""Retrieval relevance probe for Phase 0A.

Runs a small, representative query set against the live Qdrant collection
and reports, per query, the mean fused score and how many of the returned
chunks contain the expected evidence terms. This gives an objective before/
after signal when tuning the existing hybrid retriever.
"""

from __future__ import annotations

import sys

from app.core.config import get_settings
from app.services.document_service import DocumentService

# (query, one term that must appear in a good supporting chunk)
QUERY_SET = [
    ("What are the main risk factors?", "risk"),
    ("risk factors that could harm the business", "risk"),
    ("How much revenue did the company report?", "revenue"),
    ("What did the filing say about competition?", "competition"),
    ("Describe research and development spending", "research"),
    ("What are the liquidity and solvency concerns?", "liquidity"),
]


def main() -> int:
    settings = get_settings()
    service = DocumentService(settings)

    total = 0
    hits = 0
    top1 = 0
    print(f"reranker enabled : {settings.enable_reranker}")
    print(f"min similarity   : {settings.retrieval_min_similarity}")
    print("-" * 72)

    for query, term in QUERY_SET:
        try:
            context = service.retrieve(query=query, limit=5, owner_id=None)
        except Exception as exc:  # pragma: no cover - diagnostic path
            print(f"{query[:40]:42s} ERROR {type(exc).__name__}: {exc}")
            continue

        chunks = list(getattr(context, "chunks", []) or [])
        total += 1
        matched = sum(1 for c in chunks if term in c.text.lower())
        hits += 1 if matched else 0
        top1 += 1 if (chunks and term in chunks[0].text.lower()) else 0
        scores = [f"{c.score:.3f}" for c in chunks]
        print(
            f"{query[:40]:42s} n={len(chunks)} "
            f"term_hit={matched}/{len(chunks)} scores={','.join(scores)}"
        )

    print("-" * 72)
    print(f"queries with supporting evidence: {hits}/{total}")
    print(f"top-1 hit rate                  : {top1}/{total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
