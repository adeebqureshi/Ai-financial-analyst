from app.financial.analysis import FinancialAnalysisEngine
from app.financial.models import FinancialStatement


def test_analysis_engine():

    statement = FinancialStatement(
        revenue=1000,
        operating_income=250,
        net_income=200,
        total_assets=5000,
        total_liabilities=1500,
        cash=500,
        debt=700,
        shares_outstanding=100,
        free_cash_flow=250,
    )

    engine = FinancialAnalysisEngine()

    result = engine.analyze(
        statement=statement,
        current_price=15,
        growth_rate=0.08,
        risk_free_rate=0.04,
        beta=1.1,
        market_return=0.10,
        tax_rate=0.25,
        piotroski_score=9,
        altman_score=3.5,
        beneish_score=-2.5,
    )

    assert result.health_score == 100

    assert result.health_rating == "EXCELLENT"

    assert result.intrinsic_value > 0

    assert isinstance(result.recommendation, str)