from unittest.mock import MagicMock
from unittest.mock import patch
from app.financial.models import FinancialStatement
from app.orchestrator.pipeline import FinancialPipeline
@patch("app.orchestrator.pipeline.SECService")
@patch("app.orchestrator.pipeline.MarketService")
@patch("app.orchestrator.pipeline.FinancialAnalystAgent")
def test_pipeline(
    mock_analyst,
    mock_market,
    mock_sec,
):
    analyst = MagicMock()
    analyst.analyze.return_value = "analysis"
    mock_analyst.return_value = analyst
    sec = MagicMock()
    sec.get_company.return_value = "company"
    mock_sec.return_value = sec
    market = MagicMock()
    market.get_market_data.return_value = MagicMock(
        current_price=200,
    )
    mock_market.return_value = market
    pipeline = FinancialPipeline()
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
    result = pipeline.analyze_company(
        ticker="AAPL",
        statement=statement,
        query="Apple valuation",
        growth_rate=0.08,
        risk_free_rate=0.04,
        beta=1.2,
        market_return=0.10,
        tax_rate=0.25,
        piotroski_score=8,
        altman_score=3.2,
        beneish_score=-2.4,
    )
    assert result["company"] == "company"
    assert result["analysis"] == "analysis"
