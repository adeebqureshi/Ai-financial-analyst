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


def test_upload_preserves_financial_table_structure(monkeypatch, tmp_path):
    service = _make_service(monkeypatch, tmp_path)

    statement = (
        "CONSOLIDATED STATEMENT OF OPERATIONS\n"
        "Revenue | COGS | Gross Profit\n"
        "500 | 200 | 300\n"
    )

    record = _upload(
        service,
        "Apple 10-K.pdf",
        _make_pdf([statement]),
    )

    assert record["tables"] == 1

    assert record["parser_used"] == "pymupdf"

    # The structured table is stored with the page's chunk payload.
    points = service._store.get_all()

    table_payloads = [
        table
        for point in points
        for table in (point.payload or {}).get("tables", [])
    ]

    assert len(table_payloads) == 1

    assert table_payloads[0]["headers"] == [
        "Revenue",
        "COGS",
        "Gross Profit",
    ]

    assert table_payloads[0]["rows"] == [["500", "200", "300"]]

    assert table_payloads[0]["source_page"] == 1

    context = service.retrieve(
        "Gross Profit 300",
        limit=5,
        document_id=record["document_id"],
    )

    assert len(context.chunks) > 0

    text = " ".join(chunk.text for chunk in context.chunks)

    # Revenue / COGS / Gross Profit must survive as one associated unit.
    assert "Revenue" in text

    assert "COGS" in text

    assert "Gross Profit" in text


def test_upload_keeps_page_and_parser_metadata(monkeypatch, tmp_path):
    service = _make_service(monkeypatch, tmp_path)

    record = _upload(
        service,
        "Apple 10-K.pdf",
        _make_pdf(
            [
                "Apple reported record revenue this year.",
                "Supply chain risks remain elevated.",
            ]
        ),
    )

    points = service._store.get_all()

    payloads = [point.payload for point in points]

    assert all(payload.get("parser_used") == "pymupdf" for payload in payloads)

    assert all(payload.get("source", "").startswith("Apple 10-K.pdf:page-") for payload in payloads)

    pages = {payload.get("page") for payload in payloads}

    assert pages <= {1, 2}

    retrieved = service.retrieve(
        "record revenue",
        limit=5,
        document_id=record["document_id"],
    )

    for chunk in retrieved.chunks:
        assert chunk.parser_used == "pymupdf"

        assert chunk.source.startswith("Apple 10-K.pdf:page-")
