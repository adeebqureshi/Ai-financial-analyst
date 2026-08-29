"""
Security Headers Tests

Tests for production security headers middleware.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.middleware.security_headers import SecurityHeadersMiddleware
from app.core.config import Settings
from pydantic import SecretStr


def _make_app(production: bool = False) -> FastAPI:
    settings = Settings(
        auth_enabled=True,
        auth_secret_key=SecretStr("test-secret-key-0123456789abcdef0123456789abcdef"),
        auth_database_url="sqlite:///:memory:",
        environment="production" if production else "development",
    )

    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware, settings=settings)

    @app.get("/test")
    async def test_endpoint():
        return {"message": "ok"}

    return app


class TestSecurityHeadersDevelopment:
    """Test security headers in development mode."""

    def setup_method(self):
        self.client = TestClient(_make_app(production=False))

    def test_x_content_type_options(self):
        response = self.client.get("/test")
        assert response.headers["X-Content-Type-Options"] == "nosniff"

    def test_x_frame_options(self):
        response = self.client.get("/test")
        assert response.headers["X-Frame-Options"] == "DENY"

    def test_x_xss_protection(self):
        response = self.client.get("/test")
        assert response.headers["X-XSS-Protection"] == "1; mode=block"

    def test_referrer_policy(self):
        response = self.client.get("/test")
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

    def test_content_security_policy(self):
        response = self.client.get("/test")
        csp = response.headers["Content-Security-Policy"]
        assert "default-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp

    def test_permissions_policy(self):
        response = self.client.get("/test")
        permissions = response.headers["Permissions-Policy"]
        assert "camera=()" in permissions
        assert "geolocation=()" in permissions

    def test_no_hsts_in_development(self):
        response = self.client.get("/test")
        assert "Strict-Transport-Security" not in response.headers


class TestSecurityHeadersProduction:
    """Test security headers in production mode."""

    def setup_method(self):
        self.client = TestClient(_make_app(production=True))

    def test_hsts_in_production(self):
        response = self.client.get("/test")
        hsts = response.headers["Strict-Transport-Security"]
        assert "max-age=31536000" in hsts
        assert "includeSubDomains" in hsts
        assert "preload" in hsts

    def test_all_headers_present_in_production(self):
        response = self.client.get("/test")
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert "Strict-Transport-Security" in response.headers