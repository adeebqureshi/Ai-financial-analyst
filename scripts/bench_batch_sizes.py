"""Micro-benchmark embedding batch sizes in ONE warm process.

Usage: .venv/Scripts/python.exe scripts/bench_batch_sizes.py [--chunks N]
Compares batch_size 16/32/64 on identical texts, verifying identical vectors.
"""
from __future__ import annotations

import argparse
import sys
import time

sys.path.insert(0, ".")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunks", type=int, default=120)
    args = ap.parse_args()

    from app.embeddings.embedding_service import _get_model

    t0 = time.perf_counter()
    model = _get_model()
    print(f"model warm in {time.perf_counter() - t0:.2f}s")

    base = (
        "The consolidated revenue grew year over year with strong operating "
        "margin expansion driven by cloud transformation and AI services. "
        "Annualised AI revenues exceeded targets across five transformation "
        "pillars including acquisitions and productivity gains. "
    )
    texts = [f"chunk {i}: {base}" for i in range(args.chunks)]

    reference = None
    for bs in (16, 32, 64):
        # warmup + timed rep
        model.embed_batch(texts[:8], batch_size=bs)
        t0 = time.perf_counter()
        embs = model.embed_batch(texts, batch_size=bs)
        dt = time.perf_counter() - t0
        vecs = [e.vector for e in embs]
        assert len(vecs) == args.chunks and len(vecs[0]) == 384
        if reference is None:
            reference = vecs
            match = "n/a (reference)"
        else:
            maxdiff = max(
                abs(a - b) for va, vb in zip(reference, vecs) for a, b in zip(va, vb)
            )
            match = f"max_abs_diff={maxdiff:.2e}"
        print(f"batch_size={bs:<3} {dt:.2f}s "
              f"({dt / args.chunks * 1000:.1f} ms/chunk) vectors_identical: {match}")


if __name__ == "__main__":
    main()
