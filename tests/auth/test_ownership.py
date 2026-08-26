"""
Integration tests for document ownership checks (401/403 semantics).

User A uploads a document; user B must neither see it in their library nor
be able to delete it, while A retains full control.
"""

from __future__ import annotations

import io
import uuid

import fitz
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.api import register_exception_handlers
from app.auth.dependencies import get_auth_settings
from app.api.routers import api_router
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


@pytest.fixture(autouse=True)
def _isolated_library(tmp_path, monkeypatch):
    """Keep uploaded-document records out of the real storage directory."""
    monkeypatch.setattr(
        DocumentService,
        "_library_dir",
        lambda self: tmp_path / "library",
    )


@pytest.fixture()
def auth_client(tmp_path):
    settings = Settings(
        auth_enabled=True,
        auth_secret_key=SecretStr("unit-test-signing-secret-0123456789abcdef0123456789abcdef"),
        auth_database_url=f"sqlite:///{tmp_path / 'auth.db'}",
    )

    app = FastAPI()
    app.include_router(api_router)
    register_exception_handlers(app)
    app.dependency_overrides[get_auth_settings] = lambda: settings

    with TestClient(app) as client:
        yield client


def _register_and_login(client: TestClient, email: str) -> str:
    response = client.post(
        "/auth/register",
        json={"email": email, "password": "password123"},
    )

    assert response.status_code == 201, response.text

    response = client.post(
        "/auth/token",
        data={"username": email, "password": "password123"},
    )

    assert response.status_code == 200, response.text

    return response.json()["access_token"]


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


class TestDocumentOwnership:
    def test_owner_sees_and_can_delete_own_document(self, auth_client):
        token_a = _register_and_login(auth_client, "owner@example.com")

        document_id = _upload(auth_client, token_a, "Apple revenue grew.")

        listed = auth_client.get("/documents", headers=_headers(token_a))

        assert listed.status_code == 200

        ids = [doc["document_id"] for doc in listed.json()["data"]["documents"]]

        assert document_id in ids

        deleted = auth_client.delete(
            f"/documents/{document_id}",
            headers=_headers(token_a),
        )

        assert deleted.status_code == 200

    def test_other_user_cannot_delete_foreign_document(self, auth_client):
        token_a = _register_and_login(auth_client, "alice@example.com")
        token_b = _register_and_login(auth_client, "bob@example.com")

        document_id = _upload(auth_client, token_a, "Microsoft cloud growth.")

        forbidden = auth_client.delete(
            f"/documents/{document_id}",
            headers=_headers(token_b),
        )

        assert forbidden.status_code == 403

        # The document must still exist for its owner.
        still_there = auth_client.get(
            "/documents",
            headers=_headers(token_a),
        )

        ids = [
            doc["document_id"]
            for doc in still_there.json()["data"]["documents"]
        ]

        assert document_id in ids

    def test_document_library_is_scoped_per_user(self, auth_client):
        token_a = _register_and_login(auth_client, "scoped-a@example.com")
        token_b = _register_and_login(auth_client, "scoped-b@example.com")

        document_id = _upload(auth_client, token_a, "Nvidia data centers.")

        visible_to_b = auth_client.get(
            "/documents",
            headers=_headers(token_b),
        )

        assert visible_to_b.status_code == 200

        ids_for_b = [
            doc["document_id"]
            for doc in visible_to_b.json()["data"]["documents"]
        ]

        assert document_id not in ids_for_b


