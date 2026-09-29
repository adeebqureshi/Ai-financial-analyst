"""Sweep retrieval settings in one process to tune the hybrid retriever.

Each configuration reports, per query, how many returned chunks contain the
expected evidence term, and how often the single best chunk does. The
`top1` figure matters most, because a citing LLM leans on the top result.
"""

from __future__ import annotations

import sys

from app.core.config import get_settings
from app.services.document_service import DocumentService

# (label, reranker_enabled, min_similarity)
CONFIGS = [
    ("rerank=off floor=0.30 (baseline)", False, 0.30),
    ("rerank=off floor=0.00", False, 0.00),
    ("rerank=on  floor=0.30", True, 0.30),
    ("rerank=on  floor=0.15", True, 0.15),
    ("rerank=on  floor=0.00", True, 0.00),
]

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
    engine = service._engine

    # Warm the embedding model once so the sweep is not dominated by loading.
    service.retrieve(query="warm up", limit=1, owner_id=None)

    for label, rerank, floor in CONFIGS:
        engine._reranker_enabled = rerank
        engine._min_similarity = floor
        engine._reranker = None
        engine._reranker_failed = False

        hits = 0
        top1 = 0
        detail: list[str] = []
        for query, term in QUERY_SET:
            try:
                context = service.retrieve(query=query, limit=5, owner_id=None)
            except Exception as exc:  # pragma: no cover - diagnostic path
                detail.append("ERR")
                print(f"  {query[:36]:38s} ERROR {type(exc).__name__}: {exc}")
                continue
            chunks = list(getattr(context, "chunks", []) or [])
            matched = sum(1 for c in chunks if term in c.text.lower())
            hits += 1 if matched else 0
            top1 += 1 if (chunks and term in chunks[0].text.lower()) else 0
            detail.append(f"{matched}/{len(chunks)}")

        n = len(QUERY_SET)
        print(
            f"{label:34s} evidence={hits}/{n}  top1={top1}/{n}  "
            f"[{' '.join(detail)}]",
            flush=True,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
