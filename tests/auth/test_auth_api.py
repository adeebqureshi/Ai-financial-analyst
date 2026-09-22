from __future__ import annotations
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr
from app.api import register_exception_handlers
from app.auth.dependencies import get_auth_settings
from app.api.routers import api_router
from app.core.config import Settings
def _build_settings(tmp_path) -> Settings:
    return Settings(
        auth_enabled=True,
        auth_secret_key=SecretStr("unit-test-signing-secret-0123456789abcdef0123456789abcdef"),
        auth_database_url=f"sqlite:///{tmp_path / 'auth.db'}",
        access_token_expire_minutes=30,
    )
@pytest.fixture()
def auth_client(tmp_path):
    settings = _build_settings(tmp_path)
    app = FastAPI()
    app.include_router(api_router)
    register_exception_handlers(app)
    app.dependency_overrides[get_auth_settings] = lambda: settings
    with TestClient(app) as client:
        yield client
def _register(client: TestClient, email: str, password: str) -> str:
    response = client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["success"] is True
    return body["data"]["id"]
def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post(
        "/auth/token",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]
class TestRegistration:
    def test_register_returns_created_user(self, auth_client):
        response = auth_client.post(
            "/auth/register",
            json={"email": "analyst@example.com", "password": "password123"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["success"] is True
        assert body["data"]["email"] == "analyst@example.com"
        assert body["data"]["id"]
    def test_duplicate_email_conflicts(self, auth_client):
        payload = {"email": "dupe@example.com", "password": "password123"}
        assert auth_client.post("/auth/register", json=payload).status_code == 201
        assert auth_client.post("/auth/register", json=payload).status_code == 409
    def test_invalid_email_is_rejected(self, auth_client):
        response = auth_client.post(
            "/auth/register",
            json={"email": "not-an-email", "password": "password123"},
        )
        assert response.status_code == 422
    def test_short_password_is_rejected(self, auth_client):
        response = auth_client.post(
            "/auth/register",
            json={"email": "short@example.com", "password": "short"},
        )
        assert response.status_code == 422
class TestLogin:
    def test_valid_credentials_return_bearer_token(self, auth_client):
        _register(auth_client, "login@example.com", "password123")
        response = auth_client.post(
            "/auth/token",
            data={"username": "login@example.com", "password": "password123"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["token_type"] == "bearer"
        assert len(body["access_token"]) > 20
    def test_wrong_password_is_unauthorized(self, auth_client):
        _register(auth_client, "badpw@example.com", "password123")
        response = auth_client.post(
            "/auth/token",
            data={"username": "badpw@example.com", "password": "wrong-pass"},
        )
        assert response.status_code == 401
        assert response.headers.get("WWW-Authenticate") is not None
    def test_unknown_user_is_unauthorized(self, auth_client):
        response = auth_client.post(
            "/auth/token",
            data={"username": "ghost@example.com", "password": "whatever"},
        )
        assert response.status_code == 401
class TestAuthorization:
    def test_me_requires_token(self, auth_client):
        assert auth_client.get("/auth/me").status_code == 401
    def test_me_rejects_garbage_token(self, auth_client):
        response = auth_client.get(
            "/auth/me",
            headers={"Authorization": "Bearer not-a-real-token"},
        )
        assert response.status_code == 401
    def test_me_returns_authenticated_profile(self, auth_client):
        user_id = _register(auth_client, "me@example.com", "password123")
        token = _login(auth_client, "me@example.com", "password123")
        response = auth_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["id"] == user_id
        assert body["data"]["email"] == "me@example.com"
    def test_business_endpoint_requires_authentication(self, auth_client):
        response = auth_client.get("/documents")
        assert response.status_code == 401
        assert response.headers.get("WWW-Authenticate") is not None
    def test_chat_endpoint_requires_authentication(self, auth_client):
        response = auth_client.post(
            "/chat",
            json={"message": "How is Apple doing?"},
        )
        assert response.status_code == 401
    def test_protected_endpoint_accepts_valid_token(self, auth_client):
        _register(auth_client, "caller@example.com", "password123")
        token = _login(auth_client, "caller@example.com", "password123")
        response = auth_client.get(
            "/documents",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
    def test_public_endpoints_stay_open(self, auth_client):
        assert auth_client.get("/health").status_code == 200
        assert auth_client.get("/version").status_code == 200
        assert auth_client.get("/").status_code == 200