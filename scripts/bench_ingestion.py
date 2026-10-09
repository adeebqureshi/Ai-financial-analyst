"""Temporary stage-timing benchmark for the RAG ingestion pipeline.

Usage:
    .venv/Scripts/python.exe scripts/bench_ingestion.py [--pages N] [--batch-size N]

Measures separately: PDF parsing, chunking, embedding (model load + encode),
Qdrant upsert, refresh_engine, and total. Uses the real MiniLM model and an
in-memory Qdrant so results are hermetic (no server needed).
"""
from __future__ import annotations

import argparse
import io
import sys
import time
import uuid

sys.path.insert(0, ".")


def make_pdf(pages: int, words_per_page: int = 400) -> bytes:
    import fitz

    doc = fitz.open()
    lorem = (
        "The consolidated revenue grew year over year with strong operating "
        "margin expansion driven by cloud transformation and AI services. "
    )
    for i in range(pages):
        page = doc.new_page()
        # spread text so pages look like dense report pages
        body = (lorem * ((words_per_page // 15) + 1))[: words_per_page * 7]
        page.insert_textbox(fitz.Rect(72, 72, 540, 750), f"Page {i + 1}. {body}")
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, default=30)
    ap.add_argument("--batch-size", type=int, default=0,
                    help="Override embed_batch batch_size (0 = model default 16)")
    args = ap.parse_args()

    import tempfile
    from pathlib import Path

    t0 = time.perf_counter()
    pdf_bytes = make_pdf(args.pages)
    t_gen = time.perf_counter() - t0
    print(f"fixture: {args.pages} pages, {len(pdf_bytes) / 1024:.0f} KiB "
          f"(generated in {t_gen:.2f}s)")

    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.write(pdf_bytes)
    tmp.close()
    pdf_path = tmp.name

    # --- parse ---
    from app.ingestion.document_parser import UnifiedDocumentParser

    parser = UnifiedDocumentParser()
    t0 = time.perf_counter()
    result = parser.parse(pdf_path, filename="bench.pdf")
    t_parse = time.perf_counter() - t0
    pages = result.pages or [result.text]
    print(f"PDF parsing:        {t_parse:.2f}s "
          f"({len(pages)} pages, {len(result.text)} chars, "
          f"{result.parser_used}, {len(result.tables)} tables)")

    # --- chunk ---
    from app.parsers.chunker import Chunker

    chunker = Chunker(chunk_size=1000, overlap=200)
    t0 = time.perf_counter()
    chunks = chunker.chunk_pages(pages)
    t_chunk = time.perf_counter() - t0
    texts = [c.text for c in chunks]
    avg_len = sum(len(t) for t in texts) / max(len(texts), 1)
    print(f"Chunking:           {t_chunk:.2f}s ({len(chunks)} chunks, "
          f"avg {avg_len:.0f} chars)")

    # --- embedding model load ---
    from app.embeddings import embedding_service as es

    es._model = None  # force cold load for measurement
    t0 = time.perf_counter()
    model = es._get_model()
    t_load = time.perf_counter() - t0
    dim = len(model.embed("probe").vector)
    print(f"Model loading:      {t_load:.2f}s (dim={dim})")

    # --- embedding encode ---
    t0 = time.perf_counter()
    if args.batch_size:
        embs = model.embed_batch(texts, batch_size=args.batch_size)
        vectors = [list(e.vector) for e in embs]
    else:
        vectors = es.EmbeddingService().embed_documents(texts)
    t_embed = time.perf_counter() - t0
    print(f"Embedding:          {t_embed:.2f}s "
          f"({len(vectors)} vectors, batch_size={args.batch_size or 16})")

    # --- qdrant upsert (in-memory) ---
    from app.vectorstore.qdrant_store import QdrantStore

    store = QdrantStore(
        collection_name=f"bench_{uuid.uuid4().hex[:8]}",
        vector_size=dim,
    )
    import uuid as _uuid

    doc_id = _uuid.uuid4().hex
    ids = [_uuid.uuid5(_uuid.NAMESPACE_URL, f"{doc_id}:{i:06d}")
           for i in range(len(chunks))]
    payloads = [
        {"document_id": doc_id, "filename": "bench.pdf",
         "chunk_id": f"{doc_id}:{i:06d}", "page": c.page,
         "section": c.section, "text": c.text,
         "owner_id": "bench", "tenant_id": "bench"}
        for i, c in enumerate(chunks)
    ]
    t0 = time.perf_counter()
    store.upsert(ids=ids, vectors=vectors, payloads=payloads)
    t_upsert = time.perf_counter() - t0
    print(f"Qdrant indexing:    {t_upsert:.2f}s (single upsert, {len(ids)} pts)")

    # --- refresh_engine (full scroll + BM25 rebuild) ---
    from app.retrieval.retrieval_engine import RetrievalEngine

    engine = RetrievalEngine()
    # point engine at our bench store
    engine.retriever.dense.store = store
    t0 = time.perf_counter()
    engine.refresh(store, owner_id="bench")
    t_refresh = time.perf_counter() - t0
    print(f"refresh_engine:     {t_refresh:.2f}s (scroll + BM25 rebuild)")

    # --- retrieval (measures double dense search) ---
    t0 = time.perf_counter()
    ctx = engine.retrieve("consolidated revenue growth", limit=5,
                          owner_id="bench")
    t_retr = time.perf_counter() - t0
    print(f"retrieve (1 query): {t_retr:.3f}s ({len(ctx.chunks)} chunks)")

    total = t_parse + t_chunk + t_embed + t_upsert + t_refresh
    print(f"Total (parse+chunk+embed+upsert+refresh): {total:.2f}s")

    Path(pdf_path).unlink(missing_ok=True)


if __name__ == "__main__":
    main()
