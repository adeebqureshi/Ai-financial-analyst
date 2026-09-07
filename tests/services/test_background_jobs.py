"""Tests for the lightweight background-job store and background ingestion."""

import io
import json
import time
import uuid

import fitz
import pytest
from fastapi import UploadFile

from app.core.config import get_settings
from app.core.exceptions import ValidationError
from app.embeddings.embedding_service import EmbeddingService, _fallback_vector
from app.services.document_service import DocumentService
from app.services.job_store import JobStore


def _make_pdf(pages: list[str]) -> bytes:
    doc = fitz.open()

    for text in pages:
        page = doc.new_page()
        page.insert_text((72, 72), text)

    buffer = io.BytesIO()

    doc.save(buffer)

    doc.close()

    return buffer.getvalue()


def _fake_embed_documents(_self, documents):
    return [_fallback_vector(text) for text in documents]


def _fake_embed_text(_self, text):
    return _fallback_vector(text)


@pytest.fixture(autouse=True)
def _hermetic_embeddings(monkeypatch):
    monkeypatch.setattr(
        EmbeddingService,
        "embed_documents",
        _fake_embed_documents,
    )
    monkeypatch.setattr(
        EmbeddingService,
        "embed_text",
        _fake_embed_text,
    )


def _wait_until(predicate, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        if predicate():
            return True

        time.sleep(0.05)

    return False


def test_job_store_completes_successful_job(tmp_path):
    store = JobStore(tmp_path / "jobs")

    job = store.create_job("test", "owner-1")

    store.submit(job["job_id"], lambda: None)

    assert _wait_until(
        lambda: (store.get_job(job["job_id"], "owner-1") or {}).get("status")
        == "completed"
    )


def test_job_store_captures_failure_with_safe_message(tmp_path):
    store = JobStore(tmp_path / "jobs")

    job = store.create_job("test", "owner-1")

    def _boom():
        raise RuntimeError("parser exploded\nwith a very long traceback")

    store.submit(job["job_id"], _boom)

    def _failed():
        record = store.get_job(job["job_id"], "owner-1") or {}

        return record.get("status") == "failed" and record.get("error")

    assert _wait_until(_failed)

    record = store.get_job(job["job_id"], "owner-1")

    # Single line only — no multi-line internal tracebacks leak to clients.
    assert "\n" not in record["error"]

    assert record["finished_at"] is not None


def test_job_store_recovers_orphaned_jobs_on_restart(tmp_path):
    jobs_dir = tmp_path / "jobs"

    jobs_dir.mkdir(parents=True)

    # Simulate a job left "running" by a previous process.
    (jobs_dir / ("a" * 32 + ".json")).write_text(
        json.dumps(
            {
                "job_id": "a" * 32,
                "type": "document_ingestion",
                "status": "running",
                "owner_id": "owner-1",
                "payload": {},
                "error": None,
                "created_at": "2026-09-01T00:00:00+00:00",
                "started_at": "2026-09-01T00:00:01+00:00",
                "finished_at": None,
            }
        ),
        encoding="utf-8",
    )

    store = JobStore(jobs_dir)

    record = store.get_job("a" * 32, "owner-1")

    assert record["status"] == "failed"

    assert "restart" in record["error"].lower()


def test_get_job_hides_foreign_and_malformed_ids(tmp_path):
    store = JobStore(tmp_path / "jobs")

    job = store.create_job("test", "owner-1")

    assert store.get_job(job["job_id"], "owner-2") is None

    assert store.get_job("../../etc/passwd", "owner-1") is None

    assert store.get_job("", "owner-1") is None

    assert store.get_job(job["job_id"], "owner-1") is not None


# ──────────────────────────────────────────────────────────────────────────────
# Background document ingestion
# ──────────────────────────────────────────────────────────────────────────────


def _make_background_service(monkeypatch, tmp_path) -> DocumentService:
    service = DocumentService(
        get_settings(),
        collection_name=f"test_docs_{uuid.uuid4().hex[:8]}",
    )

    monkeypatch.setattr(
        DocumentService,
        "_library_dir",
        lambda self: tmp_path / "library",
    )

    monkeypatch.setattr(
        DocumentService,
        "_staging_path",
        lambda self, job_id: tmp_path / "uploads" / f"{job_id}.pdf",
    )

    monkeypatch.setattr(
        service,
        "_jobs",
        JobStore(tmp_path / "jobs"),
    )

    return service


def _upload_background(service, filename, content):
    return service.upload_background(
        UploadFile(
            filename=filename,
            file=io.BytesIO(content),
        )
    )


def test_background_upload_completes(monkeypatch, tmp_path):
    service = _make_background_service(monkeypatch, tmp_path)

    result = _upload_background(
        service,
        "AAPL 10-K.pdf",
        _make_pdf(["Revenue grew 10% in fiscal 2026."]),
    )

    assert result["status"] == "pending"

    job_id = result["job_id"]

    document_id = result["document_id"]

    # The record is visible in the library immediately as pending.
    record = service.get_document(document_id, None)

    assert record["status"] == "pending"

    assert _wait_until(
        lambda: (service.get_job(job_id, None) or {}).get("status") == "completed"
    )

    record = service.get_document(document_id, None)

    assert record["status"] == "indexed"

    assert record["chunks"] > 0

    # Staging file removed — no orphaned work.
    assert not (tmp_path / "uploads" / f"{job_id}.pdf").exists()


def test_background_upload_failure_marks_record_failed(monkeypatch, tmp_path):
    service = _make_background_service(monkeypatch, tmp_path)

    # A syntactically valid PDF header but garbage content forces the
    # parser to fail inside the background job.
    result = _upload_background(service, "bad.pdf", b"%PDF-1.4 corrupted")

    job_id = result["job_id"]

    document_id = result["document_id"]

    assert _wait_until(
        lambda: (service.get_job(job_id, None) or {}).get("status") == "failed"
    )

    record = service.get_document(document_id, None)

    assert record["status"] == "failed"

    # Staging file removed even on failure.
    assert not (tmp_path / "uploads" / f"{job_id}.pdf").exists()


def test_background_upload_rejects_invalid_input_synchronously(
    monkeypatch,
    tmp_path,
):
    service = _make_background_service(monkeypatch, tmp_path)

    with pytest.raises(ValidationError):
        _upload_background(service, "notes.txt", b"not a pdf")

    # No job was created for rejected input.
    assert list((tmp_path / "jobs").glob("*.json")) == []