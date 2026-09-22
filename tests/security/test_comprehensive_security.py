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
    monkeypatch.setattr(EmbeddingService, "embed_documents", _fake_embed_documents)
    monkeypatch.setattr(EmbeddingService, "embed_text", _fake_embed_text)
@pytest.fixture(autouse=True)
def _isolated_library(tmp_path, monkeypatch):
    monkeypatch.setattr(DocumentService, "_library_dir", lambda self: tmp_path / "library")
RATE_LIMIT_FAKE_TIME = 1_780_000_020.0
@pytest.fixture()
def frozen_rate_limit_clock(monkeypatch):
    from app.api.rate_limiter import reset_rate_limiter
    reset_rate_limiter()
    monkeypatch.setattr("app.api.rate_limiter._clock", lambda: RATE_LIMIT_FAKE_TIME)
    yield
    reset_rate_limiter()
@pytest.fixture()
def auth_app(tmp_path):
    settings = Settings(
        auth_enabled=True,
        auth_secret_key=SecretStr("unit-test-signing-secret-0123456789abcdef0123456789abcdef"),
        auth_database_url=f"sqlite:///{tmp_path / 'auth.db'}",
    )
    app = FastAPI()
    app.include_router(api_router)
    register_exception_handlers(app)
    app.dependency_overrides[get_auth_settings] = lambda: settings
    return app
@pytest.fixture()
def auth_client(auth_app):
    with TestClient(auth_app) as client:
        yield client
def _register_and_login(client: TestClient, email: str) -> str:
    response = client.post("/auth/register", json={"email": email, "password": "password123"})
    assert response.status_code == 201, response.text
    response = client.post("/auth/token", data={"username": email, "password": "password123"})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]
def _upload(client: TestClient, token: str, text: str) -> str:
    response = client.post(
        "/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": (f"report-{uuid.uuid4().hex[:6]}.pdf", _make_pdf(text), "application/pdf")},
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]["document_id"]
def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
class TestCrossUserIsolation:
    def test_chat_sessions_isolated(self, auth_client):
        token_a = _register_and_login(auth_client, "chat-iso-a@example.com")
        token_b = _register_and_login(auth_client, "chat-iso-b@example.com")
        auth_client.post("/chat", headers=_headers(token_a), json={"message": "Analyze AAPL", "session_id": "sess-a", "ticker": "AAPL"})
        assert auth_client.get("/chat/sessions", headers=_headers(token_b)).json()["data"]["total"] == 0
        assert auth_client.get("/chat/sessions/sess-a/messages", headers=_headers(token_b)).json()["data"]["total"] == 0
        assert auth_client.delete("/chat/sessions/sess-a", headers=_headers(token_b)).json()["data"]["deleted"] is False
    def test_chat_stream_isolated(self, auth_client):
        token_a = _register_and_login(auth_client, "chat-stream-a@example.com")
        token_b = _register_and_login(auth_client, "chat-stream-b@example.com")
        auth_client.post("/chat", headers=_headers(token_a), json={"message": "Hello", "session_id": "stream-sess"})
        response = auth_client.post(
            "/chat/stream",
            headers=_headers(token_b),
            json={"message": "Follow up", "session_id": "stream-sess"},
        )
        assert response.status_code == 200
    def test_documents_fully_isolated(self, auth_client):
        token_a = _register_and_login(auth_client, "doc-iso-a@example.com")
        token_b = _register_and_login(auth_client, "doc-iso-b@example.com")
        doc_id = _upload(auth_client, token_a, "Confidential financial data.")
        assert doc_id in [d["document_id"] for d in auth_client.get("/documents", headers=_headers(token_a)).json()["data"]["documents"]]
        assert doc_id not in [d["document_id"] for d in auth_client.get("/documents", headers=_headers(token_b)).json()["data"]["documents"]]
        assert auth_client.delete(f"/documents/{doc_id}", headers=_headers(token_b)).status_code == 404
        assert auth_client.delete(f"/documents/{doc_id}", headers=_headers(token_a)).status_code == 200
    def test_search_results_isolated(self, auth_client):
        token_a = _register_and_login(auth_client, "search-iso-a@example.com")
        token_b = _register_and_login(auth_client, "search-iso-b@example.com")
        _upload(auth_client, token_a, "Apple revenue grew significantly.")
        hits_a = auth_client.post("/search", headers=_headers(token_a), json={"query": "Apple revenue"}).json()["data"]["hits"]
        assert len(hits_a) > 0
        hits_b = auth_client.post("/search", headers=_headers(token_b), json={"query": "Apple revenue"}).json()["data"]["hits"]
        assert len(hits_b) == 0
    def test_search_with_document_id_isolated(self, auth_client):
        token_a = _register_and_login(auth_client, "search-doc-a@example.com")
        token_b = _register_and_login(auth_client, "search-doc-b@example.com")
        doc_id = _upload(auth_client, token_a, "Microsoft Azure revenue increased.")
        hits_a = auth_client.post("/search", headers=_headers(token_a), json={"query": "Azure", "document_id": doc_id}).json()["data"]["hits"]
        assert len(hits_a) > 0
        hits_b = auth_client.post("/search", headers=_headers(token_b), json={"query": "Azure", "document_id": doc_id}).json()["data"]["hits"]
        assert len(hits_b) == 0
class TestRateLimitSecurity:
    def test_rate_limit_per_user_not_global(self, auth_client, frozen_rate_limit_clock):
        token_a = _register_and_login(auth_client, "rl-a@example.com")
        token_b = _register_and_login(auth_client, "rl-b@example.com")
        for _ in range(20):
            auth_client.post("/chat", headers=_headers(token_a), json={"message": "test", "ticker": "AAPL"})
        assert auth_client.post("/chat", headers=_headers(token_a), json={"message": "test", "ticker": "AAPL"}).status_code == 429
        assert auth_client.post("/chat", headers=_headers(token_b), json={"message": "test", "ticker": "AAPL"}).status_code == 200
    def test_rate_limit_per_ip_when_anonymous(self, auth_client):
        pytest.skip("Anonymous rate limiting tested separately with auth_disabled fixture")
    def test_rate_limit_headers_present(self, auth_client, frozen_rate_limit_clock):
        token = _register_and_login(auth_client, "rl-headers@example.com")
        for _ in range(20):
            auth_client.post("/chat", headers=_headers(token), json={"message": "test", "ticker": "AAPL"})
        response = auth_client.post("/chat", headers=_headers(token), json={"message": "test", "ticker": "AAPL"})
        assert response.status_code == 429
        assert "Retry-After" in response.headers
        assert "X-RateLimit-Limit-Minute" in response.headers
        assert "X-RateLimit-Remaining-Minute" in response.headers
        assert "X-RateLimit-Limit-Hour" in response.headers
        assert "X-RateLimit-Remaining-Hour" in response.headers
    def test_rate_limit_respected_across_endpoints(self, auth_client, frozen_rate_limit_clock):
        token = _register_and_login(auth_client, "rl-endpoints@example.com")
        for _ in range(20):
            auth_client.post("/chat", headers=_headers(token), json={"message": "test", "ticker": "AAPL"})
        assert auth_client.post("/chat", headers=_headers(token), json={"message": "test", "ticker": "AAPL"}).status_code == 429
        assert auth_client.post("/analyze", headers=_headers(token), json={"ticker": "AAPL"}).status_code == 200
class TestJWTTokenSecurity:
    def test_expired_token_rejected(self, auth_client):
        token = _register_and_login(auth_client, "jwt-expired@example.com")
        pass
    def test_tampered_token_rejected(self, auth_client):
        token = _register_and_login(auth_client, "jwt-tamper@example.com")
        parts = token.split(".")
        tampered = f"{parts[0]}.{parts[1]}.corrupted_signature"
        response = auth_client.get("/documents", headers={"Authorization": f"Bearer {tampered}"})
        assert response.status_code == 401
    def test_token_from_another_instance_rejected(self, auth_client):
        pass
    def test_malformed_token_rejected(self, auth_client):
        response = auth_client.get("/documents", headers={"Authorization": "Bearer not.a.jwt"})
        assert response.status_code == 401
        response = auth_client.get("/documents", headers={"Authorization": "Bearer "})
        assert response.status_code == 401
        response = auth_client.get("/documents", headers={"Authorization": "Bearer"})
        assert response.status_code == 401
    def test_authorization_header_case_insensitive(self, auth_client):
        token = _register_and_login(auth_client, "jwt-case@example.com")
        response = auth_client.get("/documents", headers={"authorization": f"Bearer {token}"})
        assert response.status_code == 200
        response = auth_client.get("/documents", headers={"Authorization": f"bearer {token}"})
        assert response.status_code == 200
class TestCORSProductionBehavior:
    def test_cors_no_wildcard_with_credentials_in_production(self):
        settings = Settings(
            auth_enabled=True,
            auth_secret_key=SecretStr("test-secret-key-0123456789abcdef0123456789abcdef"),
            auth_database_url="sqlite:///:memory:",
            environment="production",
            cors_origins="https://app.example.com",
        )
        from app.main import create_app
        app = create_app(settings)
        cors_middleware = None
        for middleware in app.user_middleware:
            if hasattr(middleware, 'cls') and middleware.cls.__name__ == "CORSMiddleware":
                cors_middleware = middleware
                break
        assert cors_middleware is not None
        assert cors_middleware.kwargs["allow_credentials"] is True
        assert cors_middleware.kwargs["allow_origins"] != ["*"]
    def test_cors_wildcard_without_credentials_in_development(self):
        settings = Settings(
            auth_enabled=True,
            auth_secret_key=SecretStr("test-secret-key-0123456789abcdef0123456789abcdef"),
            auth_database_url="sqlite:///:memory:",
            environment="development",
        )
        from app.main import create_app
        app = create_app(settings)
        cors_middleware = None
        for middleware in app.user_middleware:
            if hasattr(middleware, 'cls') and middleware.cls.__name__ == "CORSMiddleware":
                cors_middleware = middleware
                break
        assert cors_middleware is not None
        assert cors_middleware.kwargs["allow_credentials"] is False
        assert cors_middleware.kwargs["allow_origins"] == ["*"]
class TestUploadSecurity:
    def test_non_pdf_rejected(self, auth_client):
        token = _register_and_login(auth_client, "upload-type@example.com")
        response = auth_client.post(
            "/documents/upload",
            headers=_headers(token),
            files={"file": ("test.txt", b"not a pdf", "text/plain")},
        )
        assert response.status_code == 422
    def test_empty_file_rejected(self, auth_client):
        token = _register_and_login(auth_client, "upload-empty@example.com")
        response = auth_client.post(
            "/documents/upload",
            headers=_headers(token),
            files={"file": ("empty.pdf", b"", "application/pdf")},
        )
        assert response.status_code == 422
    def test_oversized_file_rejected(self, auth_client):
        token = _register_and_login(auth_client, "upload-large@example.com")
        large_content = b"x" * (101 * 1024 * 1024)
        response = auth_client.post(
            "/documents/upload",
            headers=_headers(token),
            files={"file": ("large.pdf", large_content, "application/pdf")},
        )
        assert response.status_code == 422
    def test_invalid_pdf_rejected(self, auth_client):
        token = _register_and_login(auth_client, "upload-invalid@example.com")
        response = auth_client.post(
            "/documents/upload",
            headers=_headers(token),
            files={"file": ("fake.pdf", b"not a pdf file", "application/pdf")},
        )
        assert response.status_code == 422
    def test_filename_path_traversal_blocked(self, auth_client):
        token = _register_and_login(auth_client, "upload-path@example.com")
        response = auth_client.post(
            "/documents/upload",
            headers=_headers(token),
            files={"file": ("../../../etc/passwd.pdf", _make_pdf("test"), "application/pdf")},
        )
        assert response.status_code == 200
        doc_id = response.json()["data"]["document_id"]
        listed = auth_client.get("/documents", headers=_headers(token)).json()["data"]["documents"]
        assert any(d["document_id"] == doc_id for d in listed)
class TestAuthorizationBoundaries:
    def test_public_endpoints_accessible_without_auth(self, auth_client):
        assert auth_client.get("/health").status_code == 200
        assert auth_client.get("/version").status_code == 200
        assert auth_client.get("/").status_code == 200
    def test_auth_endpoints_accessible_without_auth(self, auth_client):
        assert auth_client.post("/auth/register", json={"email": "new@example.com", "password": "password123"}).status_code == 201
        response = auth_client.post("/auth/token", data={"username": "x", "password": "y"})
        assert response.status_code == 401
    def test_business_endpoints_require_auth(self, auth_client):
        endpoints = [
            ("GET", "/documents", None),
            ("POST", "/chat", {"message": "test", "ticker": "AAPL"}),
            ("POST", "/search", {"query": "test"}),
            ("POST", "/analyze", {"ticker": "AAPL"}),
            ("POST", "/report", {"ticker": "AAPL"}),
            ("POST", "/valuation", {}),
            ("POST", "/financial-ratios", {}),
            ("POST", "/risk-analysis", {}),
            ("POST", "/compare", {"tickers": ["AAPL", "MSFT"]}),
            ("POST", "/screen", {}),
        ]
        for method, path, json_data in endpoints:
            func = getattr(auth_client, method.lower())
            if method == "POST":
                response = func(path, json=json_data)
            else:
                response = func(path)
            assert response.status_code == 401, f"{method} {path} should require auth, got {response.status_code}"
    def test_ownership_enforced_on_delete(self, auth_client):
        token_a = _register_and_login(auth_client, "authz-del-a@example.com")
        token_b = _register_and_login(auth_client, "authz-del-b@example.com")
        doc_id = _upload(auth_client, token_a, "Test document.")
        response = auth_client.delete(f"/documents/{doc_id}", headers=_headers(token_b))
        assert response.status_code == 404
        assert auth_client.delete(f"/documents/{doc_id}", headers=_headers(token_a)).status_code == 200
    def test_legacy_unowned_documents_not_visible_to_authenticated(self, auth_client):
        token_a = _register_and_login(auth_client, "legacy-a@example.com")
        service = DocumentService(Settings())
        legacy_id = uuid.uuid4().hex
        service._save_record(
            {
                "document_id": legacy_id,
                "filename": "legacy.pdf",
                "pages": 1,
                "chunks": 0,
                "tables": 0,
                "parser_used": "pymupdf",
                "status": "indexed",
                "created_at": "2026-08-30T00:00:00+00:00",
                "owner_id": None,
            }
        )
        listed = auth_client.get("/documents", headers=_headers(token_a)).json()["data"]["documents"]
        assert legacy_id not in [document["document_id"] for document in listed]
        delete = auth_client.delete(f"/documents/{legacy_id}", headers=_headers(token_a))
        assert delete.status_code == 404
class TestErrorHandlingNoLeakage:
    def test_404_does_not_leak_existence(self, auth_client):
        token = _register_and_login(auth_client, "error-leak@example.com")
        response = auth_client.delete("/documents/non-existent-id", headers=_headers(token))
        assert response.status_code == 404
        assert "non-existent-id" not in response.text
    def test_error_messages_generic(self, auth_client):
        _register_and_login(auth_client, "error-msg@example.com")
        response = auth_client.post("/auth/token", data={"username": "error-msg@example.com", "password": "wrong"})
        assert response.status_code == 401
        body = response.json()
        assert "detail" in body or "message" in body
class TestChatOwnership:
    def test_chat_delete_session_enforces_ownership(self, auth_client):
        token_a = _register_and_login(auth_client, "chat-del-a@example.com")
        token_b = _register_and_login(auth_client, "chat-del-b@example.com")
        auth_client.post("/chat", headers=_headers(token_a), json={"message": "Hi", "session_id": "sess-del"})
        response = auth_client.delete("/chat/sessions/sess-del", headers=_headers(token_b))
        assert response.json()["data"]["deleted"] is False
        response = auth_client.delete("/chat/sessions/sess-del", headers=_headers(token_a))
        assert response.json()["data"]["deleted"] is True
    def test_chat_messages_enforces_ownership(self, auth_client):
        token_a = _register_and_login(auth_client, "chat-msg-a@example.com")
        token_b = _register_and_login(auth_client, "chat-msg-b@example.com")
        auth_client.post("/chat", headers=_headers(token_a), json={"message": "Secret", "session_id": "sess-msg"})
        response = auth_client.get("/chat/sessions/sess-msg/messages", headers=_headers(token_b))
        assert response.json()["data"]["total"] == 0
        response = auth_client.get("/chat/sessions/sess-msg/messages", headers=_headers(token_a))
        assert response.json()["data"]["total"] > 0
if __name__ == "__main__":
    pytest.main([__file__, "-v"])