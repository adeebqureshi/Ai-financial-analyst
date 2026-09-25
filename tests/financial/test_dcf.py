import pytest

from app.financial.dcf import DCFValuation


def test_intrinsic_value():
    value = DCFValuation.intrinsic_value(
        free_cash_flow=1000,
        growth_rate=0.10,
        discount_rate=0.12,
        terminal_growth=0.03,
        years=5,
        shares_outstanding=100,
    )
    assert value > 0


def test_invalid_discount_rate():
    with pytest.raises(ValueError):
        DCFValuation.intrinsic_value(
            free_cash_flow=1000,
            growth_rate=0.10,
            discount_rate=0.03,
            terminal_growth=0.03,
            years=5,
            shares_outstanding=100,
        )


def test_zero_shares_returns_none():
    assert DCFValuation.intrinsic_value(
        free_cash_flow=1000, growth_rate=0.10, discount_rate=0.12,
        terminal_growth=0.03, years=5, shares_outstanding=0,
    ) is None
def test_intrinsic_value_negative_fcf():
    value = DCFValuation.intrinsic_value(
        free_cash_flow=-500,
        growth_rate=0.05,
        discount_rate=0.10,
        terminal_growth=0.02,
        years=5,
        shares_outstanding=100,
    )
    assert value < 0


def test_intrinsic_value_zero_growth():
    value = DCFValuation.intrinsic_value(
        free_cash_flow=1000,
        growth_rate=0.0,
        discount_rate=0.10,
        terminal_growth=0.02,
        years=5,
        shares_outstanding=100,
    )
    assert value > 0


def test_intrinsic_value_zero_terminal_growth():
    value = DCFValuation.intrinsic_value(
        free_cash_flow=1000,
        growth_rate=0.10,
        discount_rate=0.12,
        terminal_growth=0.0,
        years=5,
        shares_outstanding=100,
    )
    assert value > 0


def test_intrinsic_value_high_growth_below_discount():
    value = DCFValuation.intrinsic_value(
        free_cash_flow=1000,
        growth_rate=0.15,
        discount_rate=0.12,
        terminal_growth=0.02,
        years=5,
        shares_outstanding=100,
    )
    assert value > 0


def test_intrinsic_value_growth_exceeds_discount_valid():
    value = DCFValuation.intrinsic_value(
        free_cash_flow=1000,
        growth_rate=0.20,
        discount_rate=0.12,
        terminal_growth=0.02,
        years=5,
        shares_outstanding=100,
    )
    assert value > 0


def test_intrinsic_value_terminal_growth_equals_discount_raises():
    with pytest.raises(ValueError, match="Discount rate must exceed terminal growth"):
        DCFValuation.intrinsic_value(
            free_cash_flow=1000,
            growth_rate=0.05,
            discount_rate=0.10,
            terminal_growth=0.10,
            years=5,
            shares_outstanding=100,
        )


def test_intrinsic_value_terminal_growth_exceeds_discount_raises():
    with pytest.raises(ValueError, match="Discount rate must exceed terminal growth"):
        DCFValuation.intrinsic_value(
            free_cash_flow=1000,
            growth_rate=0.05,
            discount_rate=0.10,
            terminal_growth=0.12,
            years=5,
            shares_outstanding=100,
        )


def test_intrinsic_value_one_year():
    value = DCFValuation.intrinsic_value(
        free_cash_flow=1000,
        growth_rate=0.10,
        discount_rate=0.12,
        terminal_growth=0.02,
        years=1,
        shares_outstanding=100,
    )
    assert value > 0


def test_intrinsic_value_many_years():
    value = DCFValuation.intrinsic_value(
        free_cash_flow=1000,
        growth_rate=0.05,
        discount_rate=0.10,
        terminal_growth=0.02,
        years=20,
        shares_outstanding=100,
    )
    assert value > 0


def test_intrinsic_value_negative_terminal_growth():
    value = DCFValuation.intrinsic_value(
        free_cash_flow=1000,
        growth_rate=0.05,
        discount_rate=0.10,
        terminal_growth=-0.01,
        years=5,
        shares_outstanding=100,
    )
    assert value > 0


def test_intrinsic_value_negative_discount_rate_raises():
    with pytest.raises(ValueError):
        DCFValuation.intrinsic_value(
            free_cash_flow=1000,
            growth_rate=0.05,
            discount_rate=-0.01,
            terminal_growth=0.02,
            years=5,
            shares_outstanding=100,
        )
