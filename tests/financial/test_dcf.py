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

    try:

        DCFValuation.intrinsic_value(
            free_cash_flow=1000,
            growth_rate=0.10,
            discount_rate=0.03,
            terminal_growth=0.03,
            years=5,
            shares_outstanding=100,
        )

    except ValueError:

        assert True

    else:

        assert False


def test_invalid_shares():

    try:

        DCFValuation.intrinsic_value(
            free_cash_flow=1000,
            growth_rate=0.10,
            discount_rate=0.12,
            terminal_growth=0.03,
            years=5,
            shares_outstanding=0,
        )

    except ValueError:

        assert True

    else:

        assert False


# ─── DCF edge cases / boundary conditions ───

def test_intrinsic_value_negative_fcf():
    """Negative FCF should still compute a value (could be negative equity value)."""
    value = DCFValuation.intrinsic_value(
        free_cash_flow=-500,
        growth_rate=0.05,
        discount_rate=0.10,
        terminal_growth=0.02,
        years=5,
        shares_outstanding=100,
    )
    # With negative FCF and positive growth, value should be negative
    assert value < 0


def test_intrinsic_value_zero_growth():
    """Zero growth rate reduces to perpetuity with no growth phase."""
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
    """Zero terminal growth is valid (no long-term growth assumption)."""
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
    """Growth rate can exceed discount rate in explicit period (finite sum converges)."""
    value = DCFValuation.intrinsic_value(
        free_cash_flow=1000,
        growth_rate=0.15,  # Higher than discount rate of 0.12 - valid for explicit period
        discount_rate=0.12,
        terminal_growth=0.02,
        years=5,
        shares_outstanding=100,
    )
    assert value > 0


def test_intrinsic_value_growth_exceeds_discount_valid():
    """Growth rate exceeding discount rate is VALID for explicit period (finite sum)."""
    value = DCFValuation.intrinsic_value(
        free_cash_flow=1000,
        growth_rate=0.20,  # Much higher than discount rate
        discount_rate=0.12,
        terminal_growth=0.02,
        years=5,
        shares_outstanding=100,
    )
    assert value > 0


def test_intrinsic_value_terminal_growth_equals_discount_raises():
    """Terminal growth rate equal to discount rate causes perpetuity divergence."""
    with pytest.raises(ValueError, match="Discount rate must exceed terminal growth"):
        DCFValuation.intrinsic_value(
            free_cash_flow=1000,
            growth_rate=0.05,
            discount_rate=0.10,
            terminal_growth=0.10,  # Equals discount rate - invalid
            years=5,
            shares_outstanding=100,
        )


def test_intrinsic_value_terminal_growth_exceeds_discount_raises():
    """Terminal growth rate exceeding discount rate is invalid."""
    with pytest.raises(ValueError, match="Discount rate must exceed terminal growth"):
        DCFValuation.intrinsic_value(
            free_cash_flow=1000,
            growth_rate=0.05,
            discount_rate=0.10,
            terminal_growth=0.12,  # Exceeds discount rate - invalid
            years=5,
            shares_outstanding=100,
        )


def test_intrinsic_value_one_year():
    """Single year projection."""
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
    """Many years of projection."""
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
    """Negative terminal growth (declining perpetuity) is valid."""
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
    """Negative discount rate with positive terminal growth is invalid."""
    # If discount_rate <= terminal_growth, raises ValueError
    with pytest.raises(ValueError):
        DCFValuation.intrinsic_value(
            free_cash_flow=1000,
            growth_rate=0.05,
            discount_rate=-0.01,
            terminal_growth=0.02,
            years=5,
            shares_outstanding=100,
        )