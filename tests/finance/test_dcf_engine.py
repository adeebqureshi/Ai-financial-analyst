from app.finance.dcf_engine import DCFEngine


def test_engine():

    engine = DCFEngine()

    valuation = engine.calculate(
        free_cash_flow=100,
        growth_rate=0.10,
        discount_rate=0.12,
        terminal_growth_rate=0.03,
        years=5,
        cash=50,
        debt=30,
        shares_outstanding=10,
    )

    assert valuation.enterprise_value > 0

    assert valuation.equity_value > 0

    assert valuation.intrinsic_value_per_share > 0