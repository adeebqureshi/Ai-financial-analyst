from app.finance.wacc_engine import WACCEngine


def test_engine():

    engine = WACCEngine()

    result = engine.calculate(
        risk_free_rate=0.04,
        beta=1.2,
        market_return=0.10,
        cost_of_debt=0.05,
        tax_rate=0.25,
        market_value_equity=800,
        market_value_debt=200,
    )

    assert round(result.cost_of_equity, 3) == 0.112

    assert round(result.after_tax_cost_of_debt, 4) == 0.0375

    assert result.wacc > 0