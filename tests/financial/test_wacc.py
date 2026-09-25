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


def test_zero_capital_returns_none():
    assert WACC.calculate(
        equity=0, debt=0, cost_of_equity=0.10, cost_of_debt=0.05, tax_rate=0.20,
    ) is None
def test_cost_of_equity_negative_beta():
    result = WACC.cost_of_equity(
        risk_free_rate=0.04,
        beta=-0.5,
        market_return=0.10,
    )
    assert result == pytest.approx(0.01, abs=1e-6)


def test_cost_of_equity_zero_beta():
    result = WACC.cost_of_equity(
        risk_free_rate=0.04,
        beta=0.0,
        market_return=0.10,
    )
    assert result == pytest.approx(0.04, abs=1e-6)


def test_cost_of_equity_zero_market_premium():
    result = WACC.cost_of_equity(
        risk_free_rate=0.05,
        beta=1.5,
        market_return=0.05,
    )
    assert result == pytest.approx(0.05, abs=1e-6)


def test_cost_of_equity_high_beta():
    result = WACC.cost_of_equity(
        risk_free_rate=0.03,
        beta=2.0,
        market_return=0.12,
    )
    assert result == pytest.approx(0.21, abs=1e-6)


def test_cost_of_equity_negative_risk_free_rate():
    result = WACC.cost_of_equity(
        risk_free_rate=-0.005,
        beta=1.0,
        market_return=0.04,
    )
    assert result == pytest.approx(0.04, abs=1e-6)


def test_after_tax_cost_of_debt_zero_tax():
    result = WACC.after_tax_cost_of_debt(cost_of_debt=0.06, tax_rate=0.0)
    assert result == pytest.approx(0.06, abs=1e-6)


def test_after_tax_cost_of_debt_high_tax():
    result = WACC.after_tax_cost_of_debt(cost_of_debt=0.10, tax_rate=0.40)
    assert result == pytest.approx(0.06, abs=1e-6)


def test_after_tax_cost_of_debt_negative_cost():
    result = WACC.after_tax_cost_of_debt(cost_of_debt=-0.01, tax_rate=0.25)
    assert result == pytest.approx(-0.0075, abs=1e-6)


def test_wacc_all_equity():
    result = WACC.calculate(
        equity=1000,
        debt=0,
        cost_of_equity=0.10,
        cost_of_debt=0.05,
        tax_rate=0.25,
    )
    assert result == pytest.approx(0.10, abs=1e-6)


def test_wacc_all_debt():
    result = WACC.calculate(
        equity=0,
        debt=1000,
        cost_of_equity=0.10,
        cost_of_debt=0.05,
        tax_rate=0.25,
    )
    assert result == pytest.approx(0.0375, abs=1e-6)


def test_wacc_negative_equity_raises():
    with pytest.raises(ValueError, match="Total capital must be positive"):
        WACC.calculate(
            equity=-100,
            debt=50,
            cost_of_equity=0.10,
            cost_of_debt=0.05,
            tax_rate=0.25,
        )


def test_wacc_high_tax_shield():
    result_low_tax = WACC.calculate(
        equity=500, debt=500, cost_of_equity=0.12, cost_of_debt=0.06, tax_rate=0.10
    )
    result_high_tax = WACC.calculate(
        equity=500, debt=500, cost_of_equity=0.12, cost_of_debt=0.06, tax_rate=0.40
    )
    assert result_high_tax < result_low_tax
