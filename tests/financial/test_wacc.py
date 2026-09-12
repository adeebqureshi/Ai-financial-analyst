import pytest

from app.financial.wacc import WACC


def test_cost_of_equity():

    result = WACC.cost_of_equity(
        risk_free_rate=0.04,
        beta=1.2,
        market_return=0.10,
    )

    assert result == pytest.approx(0.112, abs=1e-6)


def test_after_tax_cost_of_debt():

    result = WACC.after_tax_cost_of_debt(
        cost_of_debt=0.05,
        tax_rate=0.25,
    )

    assert result == pytest.approx(0.0375, abs=1e-6)


def test_wacc():

    result = WACC.calculate(
        equity=700,
        debt=300,
        cost_of_equity=0.11,
        cost_of_debt=0.05,
        tax_rate=0.25,
    )

    assert result == pytest.approx(0.08825, abs=1e-6)


def test_invalid_capital():

    with pytest.raises(ValueError):
        WACC.calculate(
            equity=0,
            debt=0,
            cost_of_equity=0.10,
            cost_of_debt=0.05,
            tax_rate=0.20,
        )


# ─── cost_of_equity edge cases ───

def test_cost_of_equity_negative_beta():
    """Negative beta produces cost of equity below risk-free rate."""
    result = WACC.cost_of_equity(
        risk_free_rate=0.04,
        beta=-0.5,
        market_return=0.10,
    )
    # 0.04 + (-0.5) * (0.10 - 0.04) = 0.04 - 0.03 = 0.01
    assert result == pytest.approx(0.01, abs=1e-6)


def test_cost_of_equity_zero_beta():
    """Zero beta means cost of equity equals risk-free rate."""
    result = WACC.cost_of_equity(
        risk_free_rate=0.04,
        beta=0.0,
        market_return=0.10,
    )
    assert result == pytest.approx(0.04, abs=1e-6)


def test_cost_of_equity_zero_market_premium():
    """Zero market risk premium (Rm = Rf) yields cost of equity = Rf regardless of beta."""
    result = WACC.cost_of_equity(
        risk_free_rate=0.05,
        beta=1.5,
        market_return=0.05,
    )
    assert result == pytest.approx(0.05, abs=1e-6)


def test_cost_of_equity_high_beta():
    """High beta amplifies market risk premium."""
    result = WACC.cost_of_equity(
        risk_free_rate=0.03,
        beta=2.0,
        market_return=0.12,
    )
    # 0.03 + 2.0 * (0.12 - 0.03) = 0.03 + 0.18 = 0.21
    assert result == pytest.approx(0.21, abs=1e-6)


def test_cost_of_equity_negative_risk_free_rate():
    """Negative risk-free rate is mathematically valid (observed in some markets)."""
    result = WACC.cost_of_equity(
        risk_free_rate=-0.005,
        beta=1.0,
        market_return=0.04,
    )
    # -0.005 + 1.0 * (0.04 - (-0.005)) = -0.005 + 0.045 = 0.04
    assert result == pytest.approx(0.04, abs=1e-6)


# ─── after_tax_cost_of_debt edge cases ───

def test_after_tax_cost_of_debt_zero_tax():
    """Zero tax rate means after-tax cost equals pre-tax cost."""
    result = WACC.after_tax_cost_of_debt(cost_of_debt=0.06, tax_rate=0.0)
    assert result == pytest.approx(0.06, abs=1e-6)


def test_after_tax_cost_of_debt_high_tax():
    """High tax rate significantly reduces after-tax cost."""
    result = WACC.after_tax_cost_of_debt(cost_of_debt=0.10, tax_rate=0.40)
    assert result == pytest.approx(0.06, abs=1e-6)


def test_after_tax_cost_of_debt_negative_cost():
    """Negative cost of debt (rare) with tax still applies."""
    result = WACC.after_tax_cost_of_debt(cost_of_debt=-0.01, tax_rate=0.25)
    assert result == pytest.approx(-0.0075, abs=1e-6)


# ─── WACC calculate edge cases ───

def test_wacc_all_equity():
    """Zero debt means WACC equals cost of equity."""
    result = WACC.calculate(
        equity=1000,
        debt=0,
        cost_of_equity=0.10,
        cost_of_debt=0.05,
        tax_rate=0.25,
    )
    assert result == pytest.approx(0.10, abs=1e-6)


def test_wacc_all_debt():
    """Zero equity means WACC equals after-tax cost of debt."""
    result = WACC.calculate(
        equity=0,
        debt=1000,
        cost_of_equity=0.10,
        cost_of_debt=0.05,
        tax_rate=0.25,
    )
    # after-tax cost = 0.05 * (1 - 0.25) = 0.0375
    assert result == pytest.approx(0.0375, abs=1e-6)


def test_wacc_negative_equity_raises():
    """Negative total capital is invalid."""
    with pytest.raises(ValueError, match="Total capital must be positive"):
        WACC.calculate(
            equity=-100,
            debt=50,
            cost_of_equity=0.10,
            cost_of_debt=0.05,
            tax_rate=0.25,
        )


def test_wacc_high_tax_shield():
    """High tax rate increases debt tax shield benefit."""
    result_low_tax = WACC.calculate(
        equity=500, debt=500, cost_of_equity=0.12, cost_of_debt=0.06, tax_rate=0.10
    )
    result_high_tax = WACC.calculate(
        equity=500, debt=500, cost_of_equity=0.12, cost_of_debt=0.06, tax_rate=0.40
    )
    assert result_high_tax < result_low_tax