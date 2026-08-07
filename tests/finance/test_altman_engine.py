from app.finance.altman_engine import AltmanEngine


def test_engine():

    engine = AltmanEngine()

    result = engine.calculate(
        working_capital=100,
        retained_earnings=200,
        ebit=150,
        market_value_equity=900,
        total_liabilities=400,
        sales=1200,
        total_assets=1000,
    )

    assert result.score > 0

    assert result.zone in (
        "Safe",
        "Grey",
        "Distress",
    )