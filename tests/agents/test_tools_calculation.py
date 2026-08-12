"""
Tests for the ``run_calculation`` tool integration in ToolRegistry.

Verifies the tool dispatches through the registry, loads real financial data
into the calculation context and returns a ToolResult carrying the
sandbox-computed value with provenance.
"""

from types import SimpleNamespace

from app.agents.tools import ToolRegistry
from app.financial.models import FinancialStatement
from app.sandbox.code_agent import CodeAgentResult, FinancialCodeAgent


def _statement() -> FinancialStatement:
    return FinancialStatement(
        revenue=394_328.0,
        operating_income=114_301.0,
        net_income=96_995.0,
        total_assets=352_583.0,
        total_liabilities=279_486.0,
        cash=30_545.0,
        debt=111_088.0,
        shares_outstanding=15_431.0,
        free_cash_flow=99_584.0,
    )


def _company_data(ticker: str = "AAPL") -> SimpleNamespace:
    return SimpleNamespace(
        ticker=ticker,
        name="Apple Inc.",
        sector="Technology",
        industry="Consumer Electronics",
        market_cap=3_000_000_000_000.0,
        description="Company description.",
        current_price=220.0,
        growth_rate=0.08,
        beta=1.2,
        tax_rate=0.21,
        piotroski_score=8,
        altman_score=3.5,
        beneish_score=-2.4,
        statement=_statement(),
    )


class FakeFinancials:
    def __init__(self, data) -> None:
        self._data = data
        self.loaded: list[str] = []

    def load(self, ticker: str):
        self.loaded.append(ticker.upper())
        return self._data


class FixedCodeAgent(FinancialCodeAgent):
    """Substitutes the LLM step so tests stay deterministic and offline."""

    def __init__(self, outcome: CodeAgentResult) -> None:
        self._outcome = outcome

    def run(self, question: str, context=None) -> CodeAgentResult:
        self.last_context = context
        return self._outcome


def _registry(code_agent) -> tuple[ToolRegistry, FakeFinancials]:
    financials = FakeFinancials(_company_data())
    registry = ToolRegistry(financials=financials, code_agent=code_agent)
    return registry, financials


def test_run_calculation_success_through_registry():
    code_agent = FixedCodeAgent(
        CodeAgentResult(success=True, code="result = 0.4 * revenue", result=157_731.2)
    )
    registry, financials = _registry(code_agent)

    result = registry.execute(
        "run_calculation",
        {"question": "What is 40% of revenue?", "ticker": "aapl"},
    )

    assert result.status == "done"
    assert result.tool == "run_calculation"

    payload = result.result
    assert payload["status"] == "computed"
    assert payload["result"] == 157_731.2
    assert payload["computed_by"] == "sandbox"
    assert payload["ticker"] == "AAPL"

    # Real financial data was loaded to build the context.
    assert financials.loaded == ["AAPL"]
    assert code_agent.last_context["revenue"] == 394_328.0


def test_run_calculation_context_contains_real_data():
    code_agent = FixedCodeAgent(CodeAgentResult(success=True, code="result = beta", result=1.2))
    registry, _ = _registry(code_agent)

    registry.execute("run_calculation", {"question": "beta?", "ticker": "AAPL"})

    assert code_agent.last_context["beta"] == 1.2
    assert code_agent.last_context["tax_rate"] == 0.21
    assert code_agent.last_context["current_price"] == 220.0
    assert code_agent.last_context["risk_free_rate"] == 0.0425
    assert code_agent.last_context["market_return"] == 0.10


def test_run_calculation_without_ticker_uses_no_financial_load():
    code_agent = FixedCodeAgent(CodeAgentResult(success=True, code="result = 2 + 2", result=4))
    registry, financials = _registry(code_agent)

    result = registry.execute(
        "run_calculation",
        {"question": "compute 2 + 2"},
    )

    assert result.status == "done"
    assert result.result["result"] == 4
    assert financials.loaded == []


def test_run_calculation_failure_returns_error_result():
    code_agent = FixedCodeAgent(
        CodeAgentResult(
            success=False,
            code="result = 1 / 0",
            error="runtime error: ZeroDivisionError: division by zero",
        )
    )
    registry, _ = _registry(code_agent)

    result = registry.execute(
        "run_calculation",
        {"question": "danger", "ticker": "AAPL"},
    )

    assert result.status == "error"
    assert result.error == "runtime error: ZeroDivisionError: division by zero"
    assert result.result["status"] == "failed"
    assert result.result["code"] == "result = 1 / 0"


def test_run_calculation_unknown_ticker_does_not_raise():
    class ExplodingFinancials(FakeFinancials):
        def load(self, ticker: str):
            raise ValueError(f"no data for {ticker}")

    registry = ToolRegistry(
        financials=ExplodingFinancials(_company_data()),
        code_agent=FixedCodeAgent(CodeAgentResult(success=True, code="result = 1", result=1)),
    )

    result = registry.execute(
        "run_calculation",
        {"question": "WACC", "ticker": "NOPE"},
    )

    assert result.status == "error"
    assert result.result is None


def test_run_calculation_listed_in_registry():
    registry, _ = _registry(
        FixedCodeAgent(CodeAgentResult(success=True, code="result = 1", result=1))
    )

    assert "run_calculation" in registry.available_tools
    assert "run_calculation" in registry._handlers


def _dummy_agent() -> FinancialCodeAgent:
    return FixedCodeAgent(CodeAgentResult(success=True, code="result = 1", result=1))
