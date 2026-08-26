"""
Regression tests: with ``AUTH_ENABLED=false`` (the test-suite default) the
pre-existing anonymous API behaviour is fully preserved.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestAuthDisabledBackwardCompatibility:
    def test_documents_endpoint_stays_anonymous(self):
        response = client.get("/documents")

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_chat_endpoint_stays_anonymous(self):
        assert client.post("/chat", json={"message": "hi"}).status_code == 200

    def test_health_remains_public(self):
        assert client.get("/health").status_code == 200