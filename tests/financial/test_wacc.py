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