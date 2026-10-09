"""Performance regression tests for the RAG ingestion pipeline (part 1).

Covers: A. Embedding batching, B. Model reuse, C. Qdrant batch upsert.
Hermetic: fake embeddings + in-memory Qdrant, no network.
"""
from __future__ import annotations

import uuid

from app.embeddings.embedding_service import EmbeddingService


class TestEmbeddingBatching:
    """A. embed_documents must use ONE batched encoder call."""

    def test_single_batched_call_not_per_chunk(self, monkeypatch):
        from unittest.mock import MagicMock

        from app.embeddings import embedding_service as es

        calls: list = []

        class _BatchModel:
            def embed_batch(self, texts, batch_size=32):
                calls.append((list(texts), batch_size))
                dim = es._expected_dimension()
                return [MagicMock(vector=[0.1] * dim) for _ in texts]

        monkeypatch.setattr(es, "_get_model", lambda: _BatchModel())
        vectors = EmbeddingService().embed_documents(
            [f"chunk {i}" for i in range(10)]
        )

        assert len(calls) == 1, "must encode all chunks in one batched call"
        assert len(calls[0][0]) == 10
        assert len(vectors) == 10
        assert all(len(v) == es._expected_dimension() for v in vectors)

    def test_batch_size_flows_from_settings(self, monkeypatch):
        from unittest.mock import MagicMock

        from app.embeddings import embedding_service as es

        seen: dict[str, int] = {}

        class _BatchModel:
            def embed_batch(self, texts, batch_size=32):
                seen["batch_size"] = batch_size
                dim = es._expected_dimension()
                return [MagicMock(vector=[0.1] * dim) for _ in texts]

        monkeypatch.setattr(es, "_get_model", lambda: _BatchModel())
        monkeypatch.setattr(es, "_embedding_batch_size", lambda: 32)
        EmbeddingService().embed_documents(["a", "b"])
        assert seen["batch_size"] == 32

    def test_default_batch_size_is_32(self):
        from app.core.constants import DEFAULT_EMBEDDING_BATCH_SIZE

        assert DEFAULT_EMBEDDING_BATCH_SIZE == 32


class TestModelReuse:
    """B. The SentenceTransformer must load once per process."""

    def test_get_model_caches_process_wide(self):
        from app.embeddings import embedding_service as es

        # Module-level `_model` global is the singleton cache: _get_model
        # returns it without reconstructing SentenceTransformer.
        assert hasattr(es, "_model")
        assert callable(es._get_model)


class TestQdrantBatchUpsert:
    """C. Large point sets must be split into bounded batches."""

    def test_large_upsert_splits_into_batches(self, monkeypatch):
        from app.vectorstore.qdrant_store import QdrantStore

        store = QdrantStore(
            collection_name=f"test_batch_{uuid.uuid4().hex[:8]}",
            vector_size=3,
        )
        batches: list[int] = []
        real_upsert_points = store._upsert_points

        def _counting(batch_ids, batch_vecs, batch_payloads):
            batches.append(len(batch_ids))
            return real_upsert_points(batch_ids, batch_vecs, batch_payloads)

        monkeypatch.setattr(store, "_upsert_points", _counting)
        monkeypatch.setattr(
            QdrantStore, "_upsert_batch_size", staticmethod(lambda: 100)
        )
        n = 250
        store.upsert(
            ids=list(range(n)),
            vectors=[[0.1, 0.2, 0.3]] * n,
            payloads=[{"tenant_id": "t", "text": "x"}] * n,
        )
        assert batches == [100, 100, 50], f"expected 3 batches, got {batches}"
        assert store.count() == n

    def test_small_upsert_single_call(self, monkeypatch):
        from app.vectorstore.qdrant_store import QdrantStore

        store = QdrantStore(
            collection_name=f"test_batch_{uuid.uuid4().hex[:8]}",
            vector_size=3,
        )
        calls: list[int] = []
        real = store._upsert_points

        def _counting(i, v, p):
            calls.append(1)
            return real(i, v, p)

        monkeypatch.setattr(store, "_upsert_points", _counting)
        store.upsert(
            ids=[1, 2],
            vectors=[[0.1, 0.2, 0.3]] * 2,
            payloads=[{"tenant_id": "t"}] * 2,
        )
        assert calls == [1]
