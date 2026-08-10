from unittest.mock import MagicMock

from app.agents.report import InvestmentReport
from app.agents.workflow_result import WorkflowResult
from app.core.config import get_settings
from app.schemas.analysis import ChatRequest
from app.services.chat_service import ChatService


def _workflow_result(
    message: str = "AAPL is trading at $220.10.",
    tickers: list[str] | None = None,
    sources: list[dict] | None = None,
    tools: list[dict] | None = None,
) -> WorkflowResult:
    report = InvestmentReport(
        company=(tickers or ["AAPL"])[0],
        title="AAPL Research",
        body=message,
    )
    return WorkflowResult(
        report=report,
        success=True,
        message=message,
        model="fake",
        sources=sources or [],
        plan=["Retrieved market data for AAPL"],
        tools_used=tools
        or [{"tool": "get_market_data", "status": "done", "detail": "Retrieved market data for AAPL"}],
        intents=["MARKET_DATA"],
        tickers=tickers or ["AAPL"],
    )


def _chat_service():
    settings = get_settings()

    coordinator = MagicMock()

    service = ChatService(settings, coordinator=coordinator)

    service._coordinator = coordinator

    return service, coordinator


def test_chat_delegates_to_coordinator_and_preserves_contract():
    service, coordinator = _chat_service()

    coordinator.run.return_value = _workflow_result()

    result = service.chat(
        ChatRequest(
            message="What is Apple's current price?",
            ticker="AAPL",
            document_id="doc1",
            session_id="s1",
        )
    )

    coordinator.run.assert_called_once_with(
        query="What is Apple's current price?",
        ticker="AAPL",
        document_id="doc1",
        session_id="s1",
    )

    assert result.message == "AAPL is trading at $220.10."

    assert result.ticker == "AAPL"

    assert result.model == "fake"


def test_chat_returns_sources():
    service, coordinator = _chat_service()

    coordinator.run.return_value = _workflow_result(
        sources=[
            {
                "document_id": "doc1",
                "filename": "Apple 10-K.pdf",
                "page": 42,
                "chunk_id": "doc1:0",
                "score": 0.9,
            }
        ],
    )

    result = service.chat(ChatRequest(message="risk"))

    assert len(result.sources) == 1

    assert result.sources[0].document_id == "doc1"

    assert result.sources[0].filename == "Apple 10-K.pdf"

    assert result.sources[0].page == 42


def test_chat_returns_tool_transparency_fields():
    service, coordinator = _chat_service()

    coordinator.run.return_value = _workflow_result()

    result = service.chat(ChatRequest(message="price"))

    assert result.plan == ["Retrieved market data for AAPL"]

    assert result.tools_used[0].tool == "get_market_data"

    assert result.tools_used[0].status == "done"

    assert result.tools_used[0].detail == "Retrieved market data for AAPL"


def test_chat_without_sources_returns_empty_citations():
    service, coordinator = _chat_service()

    coordinator.run.return_value = _workflow_result(sources=[])

    result = service.chat(ChatRequest(message="hello"))

    assert result.sources == []
