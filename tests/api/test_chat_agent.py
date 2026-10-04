import json
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
def test_chat_returns_answer_and_sources_but_never_execution_traces():
    """
    The answer and its citations are the user-facing contract. The execution
    trace -- plan steps and tool names -- must not appear in the payload, even
    though the agent ran those tools.
    """
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
    assert "plan" not in data
    assert "tools_used" not in data


def test_chat_answer_never_leaks_internal_tool_names():
    """Even if a tool name reaches the answer text, it is not surfaced as metadata."""
    app.dependency_overrides[get_chat_service] = lambda: _service(
        _workflow("Revenue was $42,279 crore.\n\nSource: Apple 10-K.pdf, p. 3.")
    )
    try:
        response = client.post(
            "/chat",
            json={"message": "What was revenue?", "session_id": "session-2"},
        )
    finally:
        app.dependency_overrides.clear()

    data = response.json()["data"]

    assert "search_documents" not in json.dumps(data)
    assert "get_market_data" not in json.dumps(data)
    assert "tools_used" not in data
    assert "plan" not in data


def test_chat_cites_only_the_pages_the_answer_names():
    """
    Retrieved-but-uncited pages are not evidence for anything, so they are not
    offered as citations.
    """
    workflow = _workflow(
        "Revenue was $383,000 million.\n\nSource: Apple 10-K.pdf, p. 42."
    )
    workflow.sources = [
        {
            "document_id": "doc1",
            "filename": "Apple 10-K.pdf",
            "page": 42,
            "chunk_id": "doc1:0",
            "score": 0.9,
        },
        {
            "document_id": "doc1",
            "filename": "Apple 10-K.pdf",
            "page": 7,
            "chunk_id": "doc1:1",
            "score": 0.8,
        },
        {
            "document_id": "doc1",
            "filename": "Apple 10-K.pdf",
            "page": 99,
            "chunk_id": "doc1:2",
            "score": 0.7,
        },
    ]
    app.dependency_overrides[get_chat_service] = lambda: _service(workflow)
    try:
        response = client.post(
            "/chat",
            json={"message": "What was revenue?", "session_id": "session-3"},
        )
    finally:
        app.dependency_overrides.clear()

    pages = [s["page"] for s in response.json()["data"]["sources"]]

    assert pages == [42]
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
        owner_id=None,
    )
def test_chat_validates_ticker():
    response = client.post(
        "/chat",
        json={"message": "price", "ticker": "TOO_LONG_TICKER"},
    )
    assert response.status_code == 422
