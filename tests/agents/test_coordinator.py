from unittest.mock import MagicMock

from app.agents.coordinator import CoordinatorAgent
from app.agents.tools import ToolResult
from app.llm.models import LLMResponse


class FakeTools:
    """Tool registry substitute with scripted results."""

    def __init__(self, results: dict[str, ToolResult]) -> None:
        self.results = results
        self.calls: list[tuple[str, dict]] = []

    def execute(self, tool, args):
        self.calls.append((tool, args))
        return self.results.get(
            tool,
            ToolResult(tool=tool, status="error", detail=f"no script for {tool}"),
        )


class FakeLLM:
    """LLM substitute returning a canned grounded answer."""

    def generate(self, request):
        return LLMResponse(text="AAPL intrinsic value is 250 based on the evidence.", model="fake")


def _coordinator(tools, analyst=None):
    coordinator = CoordinatorAgent()

    coordinator.tools = tools
    coordinator.analyst = analyst or MagicMock()

    return coordinator


def test_run_price_question_executes_market_tool_only():
    tools = FakeTools({
        "get_market_data": ToolResult(
            tool="get_market_data",
            status="done",
            detail="Retrieved live market data for AAPL",
            result={"ticker": "AAPL", "current_price": 220.10},
        ),
    })

    analyst = MagicMock()
    analyst.synthesize.return_value = ("AAPL is trading at $220.10.", "fake")

    coordinator = _coordinator(tools, analyst=analyst)

    result = coordinator.run("What is Apple's current price?")

    tool_names = [call[0] for call in tools.calls]

    assert tool_names == ["get_market_data"]

    assert "AAPL" in [call[1]["ticker"] for call in tools.calls]

    assert result.success

    assert result.tickers == ["AAPL"]

    assert result.message == "AAPL is trading at $220.10."


def test_run_valuation_question_uses_financials_and_valuation():
    tools = FakeTools({
        "get_financials": ToolResult(
            tool="get_financials",
            status="done",
            detail="Retrieved financial statements for AAPL",
            result={"ticker": "AAPL", "name": "Apple", "current_price": 220.10},
        ),
        "get_market_data": ToolResult(
            tool="get_market_data",
            status="done",
            detail="Retrieved live market data for AAPL",
            result={"ticker": "AAPL", "current_price": 220.10},
        ),
        "calculate_valuation": ToolResult(
            tool="calculate_valuation",
            status="done",
            detail="Ran DCF valuation for AAPL",
            result={
                "ticker": "AAPL",
                "current_price": 220.10,
                "intrinsic_value": 245.30,
                "upside": 11.45,
                "recommendation": "BUY",
                "discount_rate": 0.09,
            },
        ),
    })

    analyst = MagicMock()
    analyst.synthesize.return_value = ("AAPL is undervalued.", "fake")

    coordinator = _coordinator(tools, analyst=analyst)

    coordinator.run("Is Apple undervalued?")

    tool_names = [call[0] for call in tools.calls]

    assert "get_financials" in tool_names

    assert "calculate_valuation" in tool_names

    assert "search_documents" not in tool_names

    # evidence was passed to the analyst (grounded, not LLM-from-knowledge)
    _, kwargs = analyst.synthesize.call_args

    assert "calculate_valuation" in kwargs["evidence"]


def test_run_document_question_returns_sources():
    tools = FakeTools({
        "search_documents": ToolResult(
            tool="search_documents",
            status="done",
            detail="Searched Apple documents",
            result={
                "chunks": [
                    {
                        "document_id": "doc1",
                        "filename": "Apple 10-K.pdf",
                        "page": 42,
                        "text": "Apple faces supply chain concentration risk.",
                        "score": 0.9,
                    }
                ],
                "total": 1,
            },
        ),
    })

    analyst = MagicMock()
    analyst.synthesize.return_value = (
        "According to Apple 10-K.pdf (page 42), Apple faces supply chain risk.",
        "fake",
    )

    coordinator = _coordinator(tools, analyst=analyst)

    result = coordinator.run(
        "What does Apple's annual report say about supply chain risk?"
    )

    assert len(result.sources) == 1

    assert result.sources[0]["document_id"] == "doc1"

    assert result.sources[0]["page"] == 42

    assert "search_documents" in [call[0] for call in tools.calls]


def test_run_no_evidence_does_not_fabricate():
    from app.agents.financial_analyst import INSUFFICIENT_EVIDENCE_MESSAGE

    tools = FakeTools({
        "search_documents": ToolResult(
            tool="search_documents",
            status="done",
            detail="Searched Tesla documents",
            result={"chunks": [], "total": 0},
        ),
    })

    analyst = MagicMock()
    analyst.synthesize.return_value = (INSUFFICIENT_EVIDENCE_MESSAGE, None)

    coordinator = _coordinator(tools, analyst=analyst)

    result = coordinator.run(
        "What does Tesla's annual report say about CEO compensation in 2015?"
    )

    assert result.message == INSUFFICIENT_EVIDENCE_MESSAGE

    assert result.sources == []

    # The auditor must not flag a fabricated citation: nothing was claimed.
    assert result.audit is not None


def test_run_document_answer_cannot_fabricate_citation():
    tools = FakeTools({
        "search_documents": ToolResult(
            tool="search_documents",
            status="done",
            detail="Searched Apple documents",
            result={
                "chunks": [
                    {
                        "document_id": "doc1",
                        "filename": "Apple 10-K.pdf",
                        "page": 42,
                        "text": "Apple faces supply chain concentration risk.",
                        "score": 0.9,
                    }
                ],
                "total": 1,
            },
        ),
    })

    analyst = MagicMock()
    analyst.synthesize.return_value = (
        "According to Apple 10-K.pdf (page 99), Apple faces supply chain risk.",
        "fake",
    )

    coordinator = _coordinator(tools, analyst=analyst)

    result = coordinator.run(
        "What does Apple's annual report say about supply chain risk?"
    )

    # A citation to a page that was never retrieved is rejected by the auditor.
    assert result.success is False

    assert result.audit is not None

    assert result.audit.passed is False

    assert "Auditor note" in result.message


def test_run_followup_resolves_pronoun_across_turns():
    from app.agents.coordinator import CoordinatorAgent

    tools = FakeTools({})

    analyst = MagicMock()
    analyst.synthesize.return_value = ("Grounded answer.", "fake")

    coordinator = CoordinatorAgent()
    coordinator.tools = tools
    coordinator.analyst = analyst

    session = "coordinator-session-1"

    first = coordinator.run("Analyze Apple.", session_id=session)

    assert first.tickers == ["AAPL"]

    second = coordinator.run(
        "Compare it with Microsoft.",
        session_id=session,
    )

    assert second.tickers == ["AAPL", "MSFT"]

    tool_names = [call[0] for call in tools.calls]

    assert "compare_companies" in tool_names
