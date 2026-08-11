from unittest.mock import MagicMock, patch

from app.agents.financial_analyst import (
    LLM_UNAVAILABLE_MESSAGE,
    FinancialAnalystAgent,
)
from app.agents.intents import AgentIntent
from app.financial.models import FinancialStatement
from app.llm.exceptions import ProviderError


@patch("app.agents.financial_analyst.FinancialAnalysisEngine")
def test_financial_analyst(mock_engine):

    engine = MagicMock()

    engine.analyze.return_value = "analysis"

    mock_engine.return_value = engine

    agent = FinancialAnalystAgent()

    statement = FinancialStatement(
        revenue=100,
        operating_income=20,
        net_income=15,
        total_assets=500,
        total_liabilities=200,
        cash=50,
        debt=100,
        shares_outstanding=10,
        free_cash_flow=25,
    )

    result = agent.analyze(
        statement=statement,
        current_price=20,
        growth_rate=0.10,
        risk_free_rate=0.04,
        beta=1.2,
        market_return=0.10,
        tax_rate=0.25,
        piotroski_score=8,
        altman_score=3.1,
        beneish_score=-2.3,
    )

    assert result == "analysis"

    engine.analyze.assert_called_once()


class FailingLLM:
    """LLM substitute that raises a typed provider error."""

    def generate(self, request):
        raise ProviderError("OPENAI_API_KEY is not set.")


def test_synthesize_degrades_gracefully_when_llm_unavailable():
    agent = FinancialAnalystAgent()

    agent._client = FailingLLM()

    answer, model = agent.synthesize(
        query="Is Apple undervalued?",
        intents=[AgentIntent.VALUATION],
        evidence={
            "get_market_data": [
                {"result": {"ticker": "AAPL", "current_price": 220.10}}
            ]
        },
        sources=[],
        tickers=["AAPL"],
    )

    # A provider failure must not crash the request: a clean fallback is
    # returned and no model name is claimed.
    assert answer == LLM_UNAVAILABLE_MESSAGE
    assert model is None