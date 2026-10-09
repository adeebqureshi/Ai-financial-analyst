"""Indexing pipeline tests: D. pipeline, E. metadata, F. retrieval."""
from __future__ import annotations

import io
import logging
import uuid

import fitz
import pytest
from fastapi import UploadFile

from app.core.config import get_settings
from app.embeddings.embedding_service import EmbeddingService, _fallback_vector
from app.services.document_service import DocumentService


def _make_pdf(pages: list[str]) -> bytes:
    doc = fitz.open()
    for text in pages:
        page = doc.new_page()
        page.insert_text((72, 72), text)
    buffer = io.BytesIO()
    doc.save(buffer)
    doc.close()
    return buffer.getvalue()


@pytest.fixture(autouse=True)
def _hermetic2(monkeypatch):
    monkeypatch.setattr(
        EmbeddingService,
        "embed_documents",
        lambda _s, docs: [_fallback_vector(t) for t in docs],
    )
    monkeypatch.setattr(
        EmbeddingService, "embed_text", lambda _s, t: _fallback_vector(t)
    )


def _svc(monkeypatch, tmp_path) -> DocumentService:
    monkeypatch.setattr(
        DocumentService, "_library_dir", lambda self: tmp_path / "library"
    )
    settings = get_settings()
    return DocumentService(
        settings, collection_name=f"test_perf_{uuid.uuid4().hex[:8]}"
    )


def _up(svc: DocumentService, name: str, content: bytes):
    return svc.upload(UploadFile(filename=name, file=io.BytesIO(content)))


class TestIndexingPipeline:
    """D. Upload indexes fully; status=indexed only when stored."""

    def test_upload_indexes_all_chunks(self, monkeypatch, tmp_path):
        svc = _svc(monkeypatch, tmp_path)
        record = _up(
            svc,
            "Report.pdf",
            _make_pdf([f"Revenue paragraph {i} with results." for i in range(5)]),
        )
        assert record["status"] == "indexed"
        points = svc._vector_store.get_all(owner_id="anonymous")
        assert len(points) == record["chunks"] > 0

    def test_upload_logs_stage_timings(self, monkeypatch, tmp_path, caplog):
        svc = _svc(monkeypatch, tmp_path)
        with caplog.at_level(logging.INFO, logger="app.services.document_service"):
            _up(svc, "Report.pdf", _make_pdf(["Revenue grew."]))
        indexed = [r for r in caplog.records if "Indexed document" in r.message]
        assert indexed, "indexing must log per-stage timings"
        message = indexed[0].getMessage()
        for stage in ("parse=", "chunk=", "embed=", "qdrant="):
            assert stage in message


class TestMetadataPreservation:
    """E. Page/doc/filename/source metadata survives optimization."""

    def test_payload_metadata_intact(self, monkeypatch, tmp_path):
        svc = _svc(monkeypatch, tmp_path)
        record = _up(
            svc,
            "TCS Annual.pdf",
            _make_pdf(["Revenue grew 10%.", "AI services expanded."]),
        )
        points = svc._vector_store.get_all(owner_id="anonymous")
        assert len(points) == record["chunks"]
        for point in points:
            payload = point.payload
            assert payload["document_id"] == record["document_id"]
            assert payload["filename"] == "TCS Annual.pdf"
            assert payload["page"] in (1, 2)
            assert payload["source"].startswith("TCS Annual.pdf:page-")
            assert payload["parser_used"] == "pymupdf"
            assert payload["chunk_id"].startswith(record["document_id"] + ":")
            assert payload["tenant_id"] == "anonymous"


class TestRetrievalAfterIndexing:
    """F. Retrieval returns grounded chunks with citation metadata."""

    def test_retrieve_returns_cited_chunks(self, monkeypatch, tmp_path):
        from app.core import config as _cfg

        base = _cfg.settings
        monkeypatch.setattr(
            "app.core.config.get_settings",
            lambda: base.model_copy(update={"retrieval_min_similarity": 0.0}),
        )
        svc = _svc(monkeypatch, tmp_path)
        record = _up(
            svc,
            "TCS Annual.pdf",
            _make_pdf(
                [
                    "TCS consolidated revenue grew strongly in FY 2026.",
                    "AI services revenue expanded across five pillars.",
                ]
            ),
        )
        context = svc.retrieve(
            "consolidated revenue FY 2026",
            limit=5,
            document_id=record["document_id"],
        )
        assert len(context.chunks) > 0
        for chunk in context.chunks:
            assert chunk.document_id == record["document_id"]
            assert chunk.page and chunk.page >= 1
            assert chunk.source.startswith("TCS Annual.pdf:page-")
            assert chunk.text.strip()

    def test_single_dense_round_trip_per_query(self, monkeypatch, tmp_path):
        svc = _svc(monkeypatch, tmp_path)
        calls: list[int] = []
        store = svc._vector_store
        real_search = store.search

        def _counting(*args, **kwargs):
            calls.append(1)
            return real_search(*args, **kwargs)

        monkeypatch.setattr(store, "search", _counting)
        engine = svc._retrieval_engine
        engine.retriever.dense.store = store
        engine.retrieve("revenue", limit=3, owner_id="anonymous")
        assert calls == [1]

    def test_no_throwaway_refresh_on_upload(self, monkeypatch, tmp_path):
        svc = _svc(monkeypatch, tmp_path)
        refreshed: list = []
        monkeypatch.setattr(
            svc, "refresh_engine", lambda owner_id=None: refreshed.append(owner_id)
        )
        _up(svc, "Report.pdf", _make_pdf(["Revenue grew."]))
        assert refreshed == []
