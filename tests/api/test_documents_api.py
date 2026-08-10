import io

import fitz
import pytest
from fastapi.testclient import TestClient

from app.embeddings.embedding_service import EmbeddingService, _fallback_vector
from app.main import app

client = TestClient(app)


def _make_pdf(text: str) -> bytes:
    doc = fitz.open()

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


def _upload_pdf(text: str) -> str:
    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "Apple 10-K.pdf",
                _make_pdf(text),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["success"] is True

    return payload["data"]["document_id"]


def test_document_lifecycle_and_rag_chat():
    document_id = _upload_pdf(
        "Apple reported record revenue this year. "
        "Management discussed growing AI infrastructure spending."
    )

    try:
        listing = client.get("/documents").json()

        assert listing["success"] is True

        assert listing["data"]["total"] >= 1

        record = next(
            doc
            for doc in listing["data"]["documents"]
            if doc["document_id"] == document_id
        )

        assert record["filename"] == "Apple 10-K.pdf"

        assert record["pages"] == 1

        assert record["chunks"] > 0

        assert record["status"] == "indexed"

        chat = client.post(
            "/chat",
            json={
                "message": "What is this document about?",
                "document_id": document_id,
            },
        ).json()

        assert chat["success"] is True

        assert chat["data"]["message"]

        assert chat["data"]["sources"], "chat must return citations"

        source = chat["data"]["sources"][0]

        assert source["filename"] == "Apple 10-K.pdf"

        assert source["page"] == 1

        search = client.post(
            "/search",
            json={
                "query": "AI infrastructure spending",
                "limit": 3,
                "document_id": document_id,
            },
        ).json()

        assert search["success"] is True

        assert search["data"]["total"] >= 1

        assert search["data"]["hits"][0]["document_id"] == document_id

    finally:
        delete = client.delete(f"/documents/{document_id}")

        assert delete.status_code == 200

    assert client.delete(f"/documents/{document_id}").status_code == 404

    listing_after = client.get("/documents").json()

    assert all(
        doc["document_id"] != document_id
        for doc in listing_after["data"]["documents"]
    )

    chat_after = client.post(
        "/chat",
        json={
            "message": "What is this document about?",
            "document_id": document_id,
        },
    ).json()

    assert chat_after["data"]["sources"] == []


def test_upload_rejects_non_pdf():
    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "notes.txt",
                b"hello world",
                "text/plain",
            )
        },
    )

    assert response.status_code == 422
