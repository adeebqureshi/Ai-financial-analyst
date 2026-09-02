"""
Authorization / IDOR / BOLA Test Matrix

Gap-filling regression tests over the scenarios not covered by
``tests/auth/test_ownership.py`` and
``tests/security/test_comprehensive_security.py``:

- Indirect RAG access: a chat referencing a foreign document_id must never
  surface that document's content (citations) to the caller.
- Legacy / unowned chat sessions must be invisible to authenticated users.
- Parameter tampering: client-supplied ``owner_id`` fields must be ignored.
- Resource enumeration: uniform 404s for valid-format nonexistent IDs.
- Concurrent access: racing deletes by owner and non-owner stay consistent.
- 401 vs 404: unauthenticated callers get 401, never an existence hint.
"""

from __future__ import annotations

import io
import uuid
from concurrent.futures import ThreadPoolExecutor

import fitz
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.api import register_exception_handlers
from app.api.routers import api_router
from app.auth.dependencies import get_auth_settings
from app.chat.store import ChatStore
from app.core.config import Settings
from app.embeddings.embedding_service import EmbeddingService, _fallback_vector
from app.services.document_service import DocumentService


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
    monkeypatch.setattr(EmbeddingService, "embed_documents", _fake_embed_documents)
    monkeypatch.setattr(EmbeddingService, "embed_text", _fake_embed_text)


@pytest.fixture(autouse=True)
def _isolated_library(tmp_path, monkeypatch):
    monkeypatch.setattr(
        DocumentService, "_library_dir", lambda self: tmp_path / "library"
    )


@pytest.fixture()
def auth_client(tmp_path):
    settings = Settings(
        auth_enabled=True,
        auth_secret_key=SecretStr(
            "unit-test-signing-secret-0123456789abcdef0123456789abcdef"
        ),
        auth_database_url=f"sqlite:///{tmp_path / 'auth.db'}",
        chat_database_url=f"sqlite:///{tmp_path / 'chat.db'}",
    )

    app = FastAPI()
    app.include_router(api_router)
    register_exception_handlers(app)
    app.dependency_overrides[get_auth_settings] = lambda: settings

    with TestClient(app) as client:
        yield client


def _register_and_login(client: TestClient, email: str) -> str:
    response = client.post(
        "/auth/register", json={"email": email, "password": "password123"}
    )
    assert response.status_code == 201, response.text

    response = client.post(
        "/auth/token",
        data={"username": email, "password": "password123"},
    )
    assert response.status_code == 200, response.text

    return response.json()["access_token"]



class TestIndirectRAGAccess:
    """Chat / retrieval must not leak foreign documents via document_id."""

    def test_chat_with_foreign_document_id_leaks_nothing(self, auth_client):
        token_a = _register_and_login(auth_client, "rag-owner@example.com")
        token_b = _register_and_login(auth_client, "rag-attacker@example.com")

        document_id = _upload(
            auth_client, token_a, "Tesla Gigafactory production units 456000."
        )

        # Attacker references the owner's document in a chat turn.
        response = auth_client.post(
            "/chat",
            headers=_headers(token_b),
            json={
                "message": "Summarize the document",
                "document_id": document_id,
                "session_id": "rag-steal",
            },
        )
        assert response.status_code == 200

        citations = response.json()["data"]["sources"]
        assert citations == []
        assert "456000" not in response.text
        assert document_id not in response.text

    def test_chat_with_nonexistent_document_id_is_safe(self, auth_client):
        token = _register_and_login(auth_client, "rag-nonexistent@example.com")

        response = auth_client.post(
            "/chat",
            headers=_headers(token),
            json={
                "message": "Summarize the document",
                "document_id": "0" * 32,
                "session_id": "rag-missing",
            },
        )

        assert response.status_code == 200
        assert response.json()["data"]["sources"] == []

    def test_chat_stream_with_foreign_document_id_leaks_nothing(self, auth_client):
        token_a = _register_and_login(auth_client, "rag-stream-owner@example.com")
        token_b = _register_and_login(auth_client, "rag-stream-attacker@example.com")

        document_id = _upload(
            auth_client, token_a, "Nvidia data center revenue secrets 12345."
        )

        response = auth_client.post(
            "/chat/stream",
            headers=_headers(token_b),
            json={
                "message": "Summarize the document",
                "document_id": document_id,
                "session_id": "rag-stream-steal",
            },
        )

        assert response.status_code == 200
        assert "12345" not in response.text


class TestLegacyResources:
    """Legacy / unowned resources are inaccessible to authenticated users."""

    def test_legacy_chat_session_inaccessible(self, tmp_path, auth_client):
        # Seed a legacy (owner-less) session directly into the shared chat DB.
        store = ChatStore(f"sqlite:///{tmp_path / 'chat.db'}")
        store.save_turn(
            None,
            "legacy-session",
            user_message="Anonymous secret",
            assistant_message="Anonymous reply",
        )

        token = _register_and_login(auth_client, "legacy-chat@example.com")

        sessions = auth_client.get("/chat/sessions", headers=_headers(token))
        assert sessions.status_code == 200
        ids = [s["session_id"] for s in sessions.json()["data"]["sessions"]]
        assert "legacy-session" not in ids

        messages = auth_client.get(
            "/chat/sessions/legacy-session/messages", headers=_headers(token)
        )
        assert messages.status_code == 200
        assert messages.json()["data"]["total"] == 0

        deleted = auth_client.delete(
            "/chat/sessions/legacy-session", headers=_headers(token)
        )
        assert deleted.status_code == 200
        assert deleted.json()["data"]["deleted"] is False

        # The legacy record is untouched.
        _, total = store.list_messages(None, "legacy-session", page=1, page_size=10)
        assert total == 2


def _upload(client: TestClient, token: str, text: str) -> str:
    response = client.post(
        "/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={
            "file": (
                f"report-{uuid.uuid4().hex[:6]}.pdf",
                _make_pdf(text),
                "application/pdf",
            )
        },
    )
    assert response.status_code == 200, response.text

    return response.json()["data"]["document_id"]


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestParameterTampering:
    """Client-supplied ownership fields must never widen access."""

    def test_owner_id_in_request_body_is_ignored(self, auth_client):
        token_a = _register_and_login(auth_client, "tamper-a@example.com")
        token_b = _register_and_login(auth_client, "tamper-b@example.com")

        auth_client.post(
            "/chat",
            headers=_headers(token_a),
            json={"message": "A private note", "session_id": "tampered-sess"},
        )

        # B replays the same session id and tries to claim A's owner scope.
        response = auth_client.post(
            "/chat",
            headers=_headers(token_b),
            json={
                "message": "Infiltrate",
                "session_id": "tampered-sess",
                "owner_id": "tamper-a",
            },
        )
        assert response.status_code == 200

        # The write created a *separate* owner-scoped row with the same
        # session_id string — A's messages remain invisible to B.
        messages_b = auth_client.get(
            "/chat/sessions/tampered-sess/messages", headers=_headers(token_b)
        )
        assert messages_b.status_code == 200
        contents_b = [m["content"] for m in messages_b.json()["data"]["messages"]]
        assert "A private note" not in contents_b

        # A still reads exactly its own turn; B's message never mixed in.
        messages_a = auth_client.get(
            "/chat/sessions/tampered-sess/messages", headers=_headers(token_a)
        )
        contents_a = [m["content"] for m in messages_a.json()["data"]["messages"]]
        assert "Infiltrate" not in contents_a
        assert "A private note" in contents_a


class TestEnumerationAndExistence:
    """Uniform 404s; valid-format IDs cannot be enumerated."""

    def test_document_id_enumeration_returns_uniform_404(self, auth_client):
        token = _register_and_login(auth_client, "enumerate@example.com")

        bodies = set()
        for _ in range(5):
            response = auth_client.delete(
                f"/documents/{uuid.uuid4().hex}", headers=_headers(token)
            )
            assert response.status_code == 404
            body = response.json()
            body.pop("timestamp", None)  # ignore volatile fields
            bodies.add(
                (body.get("success"), body.get("message"), body.get("error"))
            )

        # Identical response content for every miss: no oracle.
        assert len(bodies) == 1

    def test_foreign_document_404_matches_missing_404(self, auth_client):
        token_a = _register_and_login(auth_client, "uniform-a@example.com")
        token_b = _register_and_login(auth_client, "uniform-b@example.com")

        document_id = _upload(auth_client, token_a, "Private earnings data.")

        foreign = auth_client.delete(
            f"/documents/{document_id}", headers=_headers(token_b)
        )
        missing = auth_client.delete(
            f"/documents/{uuid.uuid4().hex}", headers=_headers(token_b)
        )

        assert foreign.status_code == missing.status_code == 404

        foreign_body, missing_body = foreign.json(), missing.json()
        # Normalize volatile / request-scoped fields so only the authorization
        # semantics (status code, message, error code) are compared.
        for body in (foreign_body, missing_body):
            meta = body.get("metadata") or body
            if isinstance(meta, dict):
                meta.pop("timestamp", None)
                meta.pop("request_id", None)
            body.pop("timestamp", None)
            body.pop("request_id", None)
        assert foreign_body == missing_body


class TestConcurrentAccess:
    """Racing owner / non-owner deletes stay consistent."""

    def test_concurrent_delete_owner_vs_attacker(self, auth_client):
        token_a = _register_and_login(auth_client, "concurrent-a@example.com")
        token_b = _register_and_login(auth_client, "concurrent-b@example.com")

        document_id = _upload(auth_client, token_a, "Concurrent document.")

        def delete(token: str) -> int:
            return auth_client.delete(
                f"/documents/{document_id}", headers=_headers(token)
            ).status_code

        with ThreadPoolExecutor(max_workers=8) as pool:
            codes = list(pool.map(delete, [token_a, token_b] * 4))

        # Only the owner's single successful delete is possible; every other
        # attempt (attacker or already-deleted) is a uniform 404.
        assert codes.count(200) <= 1
        assert all(code in (200, 404) for code in codes)

        # Regardless of interleaving, the document ends up gone for the
        # owner and never visible to the attacker.
        remaining = auth_client.get("/documents", headers=_headers(token_a))
        ids = [d["document_id"] for d in remaining.json()["data"]["documents"]]
        assert document_id not in ids


class TestUnauthenticatedSemantics:
    """401 without credentials; 404 never leaks existence of owned items."""

    def test_unauthenticated_gets_401_not_404(self, auth_client):
        # A resource that DOES exist, owned by a logged-in user:
        token = _register_and_login(auth_client, "unauth-sem@example.com")
        document_id = _upload(auth_client, token, "Existing document.")

        for method, path in (
            ("get", "/documents"),
            ("delete", f"/documents/{document_id}"),
            ("get", "/chat/sessions"),
            ("get", "/chat/sessions/x/messages"),
            ("delete", "/chat/sessions/x"),
            ("post", "/search"),
            ("post", "/chat"),
        ):
            if method == "post":
                response = getattr(auth_client, method)(
                    path, json={"query": "x", "message": "x"}
                )
            else:
                response = getattr(auth_client, method)(path)
            assert response.status_code == 401, (
                f"{method} {path}: {response.status_code}"
            )
            # No hint about whether the resource exists.
            assert document_id not in response.text

