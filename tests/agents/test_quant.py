from unittest.mock import MagicMock, patch

from app.agents.quant import QuantAgent
from app.financial.data import CompanyFinancialData
from app.financial.models import FinancialStatement


def test_quant():
    agent = QuantAgent()

    # Mock the financial data service to return predictable data
    mock_statement = FinancialStatement(
        revenue=1000.0,
        operating_income=250.0,
        net_income=200.0,
        total_assets=1000.0,
        total_liabilities=600.0,
        cash=100.0,
        debt=300.0,
        shares_outstanding=10.0,
        free_cash_flow=150.0,
        gross_profit=500.0,
    )

    mock_data = CompanyFinancialData(
        ticker="AAPL",
        statement=mock_statement,
        piotroski_score=7,
        altman_score=3.5,
        beneish_score=-2.5,
        growth_rate=0.10,
        beta=1.2,
        tax_rate=0.21,
        current_price=150.0,
        name="Apple Inc.",
        sector="Technology",
        industry="Consumer Electronics",
        market_cap=2_500_000.0,
        description="Apple Inc. designs, manufactures, and markets smartphones.",
    )

    with patch.object(agent.financial_data, "load", return_value=mock_data):
        result = agent.analyze("AAPL")

    assert result.company == "AAPL"
    assert result.metric_count == 7
    # current_ratio = current_assets / current_liabilities = (1000*0.3) / (600*0.3) = 300/180 = 1.666...
    assert abs(result.metrics["current_ratio"] - 1.6666666666666667) < 0.001
    # debt_to_equity = total_liabilities / equity = 600 / (1000-600) = 600/400 = 1.5
    assert abs(result.metrics["debt_to_equity"] - 1.5) < 0.001
    # return_on_assets = net_income / total_assets = 200/1000 = 0.2
    assert abs(result.metrics["return_on_assets"] - 0.2) < 0.001
    # return_on_equity = net_income / equity = 200/400 = 0.5
    assert abs(result.metrics["return_on_equity"] - 0.5) < 0.001
    # gross_margin = gross_profit / revenue = 500/1000 = 0.5
    assert abs(result.metrics["gross_margin"] - 0.5) < 0.001
    # operating_margin = operating_income / revenue = 250/1000 = 0.25
    assert abs(result.metrics["operating_margin"] - 0.25) < 0.001
    # net_margin = net_income / revenue = 200/1000 = 0.2
    assert abs(result.metrics["net_margin"] - 0.2) < 0.001