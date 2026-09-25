import pytest

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


def test_cagr_zero_years_returns_none():
    assert GrowthMetrics.cagr(100, 200, 0) is None


def test_cagr_negative_years_raises():
    with pytest.raises(ValueError, match="Years must be positive"):
        GrowthMetrics.cagr(100, 200, -1)


def test_cagr_zero_beginning_returns_none():
    assert GrowthMetrics.cagr(0, 200, 5) is None


def test_cagr_negative_beginning_raises():
    with pytest.raises(ValueError, match="Beginning value must be positive"):
        GrowthMetrics.cagr(-100, 200, 5)


def test_cagr_equal_start_end():
    assert GrowthMetrics.cagr(100, 100, 5) == 0.0


def test_cagr_declining_value():
    result = GrowthMetrics.cagr(200, 100, 5)
    assert result < 0
    assert round(result, 3) == -0.129


def test_cagr_one_year():
    assert GrowthMetrics.cagr(100, 120, 1) == pytest.approx(0.20, abs=1e-10)


def test_cagr_large_growth():
    result = GrowthMetrics.cagr(100, 10000, 10)
    assert result > 0.5


def test_growth_rate_zero_previous_returns_none():
    assert GrowthMetrics.growth_rate(0, 100) is None


def test_growth_rate_negative_previous_raises():
    with pytest.raises(ValueError, match="Previous value must be positive"):
        GrowthMetrics.growth_rate(-100, 100)


def test_growth_rate_declining():
    assert GrowthMetrics.growth_rate(100, 80) == -0.20


def test_growth_rate_equal_values():
    assert GrowthMetrics.growth_rate(100, 100) == 0.0


def test_growth_rate_large_increase():
    assert GrowthMetrics.growth_rate(100, 500) == 4.0
