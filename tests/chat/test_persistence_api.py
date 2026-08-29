"""
API-level persistence and ownership tests for chat.

The full chat API is wired against a real (temporary) SQLite chat store with a
fake coordinator, so a completed conversation is actually persisted and is
ownership-isolated across authenticated users.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.api import register_exception_handlers
from app.api.dependencies.services import get_chat_service
from app.api.routers import api_router
from app.agents.report import InvestmentReport
from app.agents.workflow_result import WorkflowResult
from app.auth.dependencies import get_auth_settings
from app.chat.store import ChatStore
from app.core.config import Settings
from app.services.chat_service import ChatService


def test_chat_turn_is_persisted_and_ownership_isolated(tmp_path):
    app, _ = _make_app(tmp_path)

    with TestClient(app) as client:
        token_a = _register_and_login(client, "alice@example.com")
        token_b = _register_and_login(client, "bob@example.com")

        # Alice has a two-turn conversation in one session.
        response = client.post(
            "/chat",
            headers=_headers(token_a),
            json={"message": "Analyze Apple", "ticker": "AAPL", "session_id": "sess-a"},
        )
        assert response.status_code == 200, response.text
        assert response.json()["data"]["message"] == "Answer for: Analyze Apple"

        response = client.post(
            "/chat",
            headers=_headers(token_a),
            json={"message": "And its valuation?", "ticker": "AAPL", "session_id": "sess-a"},
        )
        assert response.status_code == 200

        # Alice sees exactly her one session with four messages.
        listed = client.get("/chat/sessions", headers=_headers(token_a))
        assert listed.status_code == 200
        body = listed.json()["data"]
        assert body["total"] == 1
        assert body["sessions"][0]["session_id"] == "sess-a"
        assert body["sessions"][0]["updated_at"] is not None

        messages = client.get("/chat/sessions/sess-a/messages", headers=_headers(token_a))
        assert messages.status_code == 200
        msg_body = messages.json()["data"]
        assert msg_body["total"] == 4
        roles = [m["role"] for m in msg_body["messages"]]
        assert roles == ["user", "assistant", "user", "assistant"]

        # Persisted metadata is retained (model + plan).
        assistant = msg_body["messages"][1]
        assert assistant["metadata"]["model"] == "fake-model"
        assert assistant["metadata"]["plan"] == ["Retrieved market data for AAPL"]

        # Bob sees neither the session nor its messages.
        bob_listed = client.get("/chat/sessions", headers=_headers(token_b))
        assert bob_listed.json()["data"]["total"] == 0

        bob_messages = client.get("/chat/sessions/sess-a/messages", headers=_headers(token_b))
        assert bob_messages.json()["data"]["total"] == 0

        # Bob cannot delete Alice's session.
        forbidden = client.delete("/chat/sessions/sess-a", headers=_headers(token_b))
        assert forbidden.status_code == 200
        assert forbidden.json()["data"]["deleted"] is False

        # Alice can.
        own_delete = client.delete("/chat/sessions/sess-a", headers=_headers(token_a))
        assert own_delete.json()["data"]["deleted"] is True

        remaining = client.get("/chat/sessions", headers=_headers(token_a))
        assert remaining.json()["data"]["total"] == 0


def test_anonymous_requests_are_isolated_when_auth_disabled(tmp_path):
    settings = Settings(
        auth_enabled=False,
        auth_database_url=f"sqlite:///{tmp_path / 'auth-off.db'}",
        chat_database_url=f"sqlite:///{tmp_path / 'chat-off.db'}",
    )

    app = FastAPI()
    app.include_router(api_router)
    register_exception_handlers(app)
    app.dependency_overrides[get_auth_settings] = lambda: settings

    store = ChatStore(settings.chat_database_url)
    service = ChatService(settings, coordinator=_FakeCoordinator(), store=store)
    app.dependency_overrides[get_chat_service] = lambda: service

    with TestClient(app) as client:
        response = client.post(
            "/chat",
            json={"message": "Hi", "session_id": "dev-session"},
        )
        assert response.status_code == 200, response.text

        listed = client.get("/chat/sessions")
        assert listed.json()["data"]["total"] == 1

        messages = client.get("/chat/sessions/dev-session/messages")
        assert messages.json()["data"]["total"] == 2


class _FakeCoordinator:
    """Deterministic coordinator double for persistence tests."""

    def __init__(self) -> None:
        self.calls = []

    def hydrate_context(self, session_id, tickers, query, answer) -> None:
        return None

    def run(self, **kwargs) -> WorkflowResult:
        self.calls.append(kwargs)
        query = kwargs.get("query", "")
        report = InvestmentReport(
            company="AAPL",
            title="AAPL Research",
            body=f"Answer for: {query}",
        )
        return WorkflowResult(
            report=report,
            success=True,
            message=report.body,
            model="fake-model",
            sources=[],
            plan=["Retrieved market data for AAPL"],
            tools_used=[
                {"tool": "get_market_data", "status": "done", "detail": "Retrieved market data for AAPL"}
            ],
            intents=["MARKET_DATA"],
            tickers=["AAPL"],
        )


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


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _make_app(tmp_path):
    settings = Settings(
        auth_enabled=True,
        auth_secret_key=SecretStr("unit-test-signing-secret-0123456789abcdef0123456789abcdef"),
        auth_database_url=f"sqlite:///{tmp_path / 'auth.db'}",
        chat_database_url=f"sqlite:///{tmp_path / 'chat.db'}",
    )

    app = FastAPI()
    app.include_router(api_router)
    register_exception_handlers(app)
    app.dependency_overrides[get_auth_settings] = lambda: settings

    store = ChatStore(settings.chat_database_url)
    service = ChatService(settings, coordinator=_FakeCoordinator(), store=store)
    app.dependency_overrides[get_chat_service] = lambda: service

    return app, store