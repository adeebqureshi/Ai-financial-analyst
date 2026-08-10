import io
import uuid

import fitz
import pytest

from app.core.config import get_settings
from app.core.exceptions import ValidationError
from app.embeddings.embedding_service import EmbeddingService, _fallback_vector
from app.services.document_service import DocumentService


def _make_pdf(pages: list[str]) -> bytes:
    """Render a multi-page PDF in memory."""
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


def _make_service(monkeypatch, tmp_path) -> DocumentService:
    settings = get_settings()

    service = DocumentService(
        settings,
        collection_name=f"test_docs_{uuid.uuid4().hex[:8]}",
    )

    monkeypatch.setattr(
        DocumentService,
        "_library_dir",
        lambda self: tmp_path / "library",
    )

    return service


def _upload(service: DocumentService, filename: str, content: bytes):
    from fastapi import UploadFile

    return service.upload(
        UploadFile(
            filename=filename,
            file=io.BytesIO(content),
        )
    )


def test_upload_indexes_document(monkeypatch, tmp_path):
    service = _make_service(monkeypatch, tmp_path)

    record = _upload(
        service,
        "Annual Report.pdf",
        _make_pdf(
            [
                "Apple reported record revenue this year.",
                "Supply chain risks remain elevated.",
            ]
        ),
    )

    assert record["status"] == "indexed"

    assert record["pages"] == 2

    assert record["chunks"] > 0

    assert record["filename"] == "Annual Report.pdf"

    listing = service.list_documents()

    assert listing["total"] == 1

    assert listing["documents"][0]["document_id"] == record["document_id"]


def test_upload_rejects_non_pdf(monkeypatch, tmp_path):
    service = _make_service(monkeypatch, tmp_path)

    with pytest.raises(ValidationError):
        _upload(service, "notes.txt", b"hello")


def test_upload_rejects_invalid_content(monkeypatch, tmp_path):
    service = _make_service(monkeypatch, tmp_path)

    with pytest.raises(ValidationError):
        _upload(service, "fake.pdf", b"not a pdf")


def test_retrieval_returns_citations(monkeypatch, tmp_path):
    service = _make_service(monkeypatch, tmp_path)

    record = _upload(
        service,
        "Apple 10-K.pdf",
        _make_pdf(
            [
                "Apple faces supply chain risks.",
                "Management discussed AI infrastructure spending.",
            ]
        ),
    )

    context = service.retrieve(
        "What are Apple's biggest risks?",
        limit=3,
        document_id=record["document_id"],
    )

    assert len(context.chunks) > 0

    for chunk in context.chunks:
        assert chunk.document_id == record["document_id"]

        assert chunk.filename == "Apple 10-K.pdf"

        assert chunk.page is not None

        assert chunk.page >= 1

    assert context.chunks[0].page in (1, 2)


def test_retrieval_scoped_to_document(monkeypatch, tmp_path):
    service = _make_service(monkeypatch, tmp_path)

    record_a = _upload(
        service,
        "Apple 10-K.pdf",
        _make_pdf(["Apple supply chain risk."]),
    )

    _upload(
        service,
        "Microsoft 10-K.pdf",
        _make_pdf(["Microsoft cloud revenue."]),
    )

    context = service.retrieve(
        "Apple supply chain risk",
        limit=5,
        document_id=record_a["document_id"],
    )

    assert len(context.chunks) > 0

    for chunk in context.chunks:
        assert chunk.document_id == record_a["document_id"]


def test_delete_removes_vectors(monkeypatch, tmp_path):
    service = _make_service(monkeypatch, tmp_path)

    record = _upload(
        service,
        "Apple 10-K.pdf",
        _make_pdf(["Apple revenue."]),
    )

    service.delete_document(record["document_id"])

    assert service.list_documents()["total"] == 0

    context = service.retrieve("Apple", limit=5)

    assert len(context.chunks) == 0


def test_global_retrieval_across_documents(monkeypatch, tmp_path):
    service = _make_service(monkeypatch, tmp_path)

    _upload(
        service,
        "Apple 10-K.pdf",
        _make_pdf(["Apple supply chain risk in China."]),
    )

    _upload(
        service,
        "Microsoft 10-K.pdf",
        _make_pdf(["Microsoft cloud revenue growth."]),
    )

    context = service.retrieve("cloud revenue growth", limit=5)

    assert len(context.chunks) > 0
