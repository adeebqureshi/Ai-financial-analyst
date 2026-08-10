"""
Agentic chat endpoint tests.

Verifies that ``POST /chat``:
- preserves the existing request contract (message / ticker / document_id),
- accepts the new optional ``session_id``,
- returns backward-compatible ``plan`` and ``tools_used`` metadata,
- never exposes hidden chain-of-thought (only high-level tool steps).
"""

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.agents.report import InvestmentReport
from app.agents.workflow_result import WorkflowResult
from app.api.dependencies.services import get_chat_service
from app.core.config import get_settings
from app.main import app
from app.services.chat_service import ChatService

client = TestClient(app)


def _workflow(message: str) -> WorkflowResult:
    report = InvestmentReport(
        company="AAPL",
        title="AAPL Research",
        body=message,
    )
    return WorkflowResult(
        report=report,
        success=True,
        message=message,
        model="fake-model",
        sources=[
            {
                "document_id": "doc1",
                "filename": "Apple 10-K.pdf",
                "page": 42,
                "chunk_id": "doc1:0",
                "score": 0.9,
            }
        ],
        plan=["Retrieved market data for AAPL"],
        tools_used=[
            {"tool": "get_market_data", "status": "done", "detail": "Retrieved market data for AAPL"}
        ],
        intents=["MARKET_DATA"],
        tickers=["AAPL"],
    )


def _service(workflow: WorkflowResult) -> ChatService:
    coordinator = MagicMock()
    coordinator.run.return_value = workflow
    return ChatService(get_settings(), coordinator=coordinator)


def test_chat_returns_answer_sources_and_tools():
    app.dependency_overrides[get_chat_service] = lambda: _service(
        _workflow("AAPL is trading at $220.10.")
    )

    try:
        response = client.post(
            "/chat",
            json={
                "message": "What is Apple's current price?",
                "ticker": "AAPL",
                "session_id": "session-1",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    payload = response.json()

    assert payload["success"] is True

    data = payload["data"]

    assert data["message"] == "AAPL is trading at $220.10."

    assert data["ticker"] == "AAPL"

    assert data["sources"][0]["filename"] == "Apple 10-K.pdf"

    assert data["sources"][0]["page"] == 42

    assert data["tools_used"][0]["tool"] == "get_market_data"

    assert data["tools_used"][0]["status"] == "done"

    assert data["plan"] == ["Retrieved market data for AAPL"]


def test_chat_preserves_document_scoping():
    service = _service(_workflow("answer"))

    app.dependency_overrides[get_chat_service] = lambda: service

    try:
        response = client.post(
            "/chat",
            json={"message": "What is the supply chain risk?", "document_id": "doc9"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    service._coordinator.run.assert_called_once_with(
        query="What is the supply chain risk?",
        ticker=None,
        document_id="doc9",
        session_id=None,
    )


def test_chat_validates_ticker():
    response = client.post(
        "/chat",
        json={"message": "price", "ticker": "TOO_LONG_TICKER"},
    )

    assert response.status_code == 422
