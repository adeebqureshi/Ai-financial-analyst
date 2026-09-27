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
from app.core import config as _app_core_config
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


def _settings_with_no_similarity_floor(_base):
    base = _app_core_config.settings
    return base.model_copy(update={"retrieval_min_similarity": 0.0})


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
    _real_get_settings = _app_core_config.get_settings
    monkeypatch.setattr(
        "app.core.config.get_settings",
        lambda: _settings_with_no_similarity_floor(_real_get_settings()),
    )


@pytest.fixture(autouse=True)
def _isolated_library(tmp_path, monkeypatch):
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


class TestDocumentAuthorization:
    """Focused coverage for document ownership enforcement.

    A. owner can access their own document
    B. another authenticated user cannot access it
    C. another authenticated user cannot delete it
    D. anonymous callers are denied protected document operations
    """

    def test_a_owner_can_access_own_document(self, auth_client):
        token_a = _register_and_login(auth_client, "authz-owner-a@example.com")
        document_id = _upload(auth_client, token_a, "ACME revenue was 4.8 billion.")

        listed = auth_client.get("/documents", headers=_headers(token_a))
        assert listed.status_code == 200
        ids = [doc["document_id"] for doc in listed.json()["data"]["documents"]]
        assert document_id in ids

    def test_b_other_user_cannot_see_foreign_document(self, auth_client):
        token_a = _register_and_login(auth_client, "authz-owner-b@example.com")
        token_b = _register_and_login(auth_client, "authz-other-b@example.com")
        document_id = _upload(auth_client, token_a, "ACME net income was 612 million.")

        listed = auth_client.get("/documents", headers=_headers(token_b))
        assert listed.status_code == 200
        ids = [doc["document_id"] for doc in listed.json()["data"]["documents"]]
        assert document_id not in ids

    def test_c_other_user_cannot_delete_foreign_document(self, auth_client):
        token_a = _register_and_login(auth_client, "authz-owner-c@example.com")
        token_b = _register_and_login(auth_client, "authz-other-c@example.com")
        document_id = _upload(auth_client, token_a, "ACME gross margin was 41.3 percent.")

        denied = auth_client.delete(
            f"/documents/{document_id}",
            headers=_headers(token_b),
        )
        assert denied.status_code == 404

        still_owned = auth_client.get("/documents", headers=_headers(token_a))
        ids = [doc["document_id"] for doc in still_owned.json()["data"]["documents"]]
        assert document_id in ids

    def test_d_anonymous_cannot_list_or_delete_documents(self, auth_client):
        token_a = _register_and_login(auth_client, "authz-owner-d@example.com")
        document_id = _upload(auth_client, token_a, "ACME total debt was 1.95 billion.")

        anonymous_list = auth_client.get("/documents")
        assert anonymous_list.status_code == 401

        anonymous_delete = auth_client.delete(f"/documents/{document_id}")
        assert anonymous_delete.status_code == 401

        still_owned = auth_client.get("/documents", headers=_headers(token_a))
        ids = [doc["document_id"] for doc in still_owned.json()["data"]["documents"]]
        assert document_id in ids
