from app.financial.growth import GrowthMetrics


def test_growth_rate():

    growth = GrowthMetrics.growth_rate(
        100,
        120,
    )

    assert round(growth, 2) == 0.20


def test_revenue_growth():

    growth = GrowthMetrics.revenue_growth(
        200,
        250,
    )

    assert round(growth, 2) == 0.25


def test_earnings_growth():

    growth = GrowthMetrics.earnings_growth(
        80,
        100,
    )

    assert round(growth, 2) == 0.25


def test_fcf_growth():

    growth = GrowthMetrics.free_cash_flow_growth(
        50,
        75,
    )

    assert round(growth, 2) == 0.50


def test_cagr():

    growth = GrowthMetrics.cagr(
        100,
        200,
        5,
    )

    assert round(growth, 3) == 0.149