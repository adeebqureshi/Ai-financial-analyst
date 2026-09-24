import io
import fitz
import pytest
from fastapi.testclient import TestClient
from app.embeddings.embedding_service import EmbeddingService, _fallback_vector
from app.main import app
from app.auth.dependencies import get_current_user
from app.api.dependencies.services import get_search_service
from app.core.exceptions import RetrievalError


class MockUser:
    id = "test_user_123"


@pytest.fixture()
def authed_client():
    app.dependency_overrides[get_current_user] = lambda: MockUser()
    try:
        with TestClient(app) as tc:
            yield tc
    finally:
        app.dependency_overrides.pop(get_current_user, None)
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
def _upload_pdf(client, text: str) -> str:
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
def test_document_lifecycle_and_rag_chat(authed_client):
    client = authed_client
    document_id = _upload_pdf(
        client,
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
@pytest.mark.parametrize(
    ("message", "error_code"),
    [
        (
            "Document search is temporarily unavailable.",
            "VECTOR_STORE_UNAVAILABLE",
        ),
        (
            "Document search returned an invalid response.",
            "VECTOR_STORE_INVALID_RESPONSE",
        ),
    ],
)
def test_search_maps_qdrant_failures_to_safe_502(
    authed_client,
    message,
    error_code,
):
    class FailingSearchService:
        def search(self, request, owner_id=None):
            raise RetrievalError(message, error_code=error_code)

    app.dependency_overrides[get_search_service] = lambda: FailingSearchService()
    try:
        response = authed_client.post(
            "/search",
            json={"query": "revenue", "limit": 3},
        )
    finally:
        app.dependency_overrides.pop(get_search_service, None)

    assert response.status_code == 502
    payload = response.json()
    assert payload["success"] is False
    assert payload["message"] == message
    assert payload["errors"][0]["code"] == error_code
    assert "qdrant" not in response.text.lower()
    assert "traceback" not in response.text.lower()


def test_upload_rejects_non_pdf(authed_client):
    response = authed_client.post(
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