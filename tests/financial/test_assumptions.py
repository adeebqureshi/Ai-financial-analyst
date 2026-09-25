from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from app.financial.assumptions import (
    DEFAULT_COST_OF_DEBT,
    DEFAULT_MARKET_RETURN,
    DEFAULT_PROJECTION_YEARS,
    DEFAULT_RISK_FREE_RATE,
    DEFAULT_TAX_RATE,
    DEFAULT_TERMINAL_GROWTH,
    FinancialAssumptions,
    get_financial_assumptions,
    with_request_overrides,
)


class TestFinancialAssumptionsValidation:
    def _valid(self, **overrides) -> dict:
        data = {
            "risk_free_rate": DEFAULT_RISK_FREE_RATE,
            "market_return": DEFAULT_MARKET_RETURN,
            "cost_of_debt": DEFAULT_COST_OF_DEBT,
            "tax_rate": DEFAULT_TAX_RATE,
            "terminal_growth": DEFAULT_TERMINAL_GROWTH,
            "projection_years": DEFAULT_PROJECTION_YEARS,
        }
        data.update(overrides)
        return data

    def test_valid_defaults_construct(self) -> None:
        a = FinancialAssumptions(**self._valid())
        assert a.risk_free_rate == 0.0425
        assert a.market_return == 0.10
        assert a.is_assumption is True

    def test_negative_risk_free_rate_rejected(self) -> None:
        with pytest.raises(ValidationError):
            FinancialAssumptions(**self._valid(risk_free_rate=-0.01))

    def test_risk_free_rate_above_bound_rejected(self) -> None:
        with pytest.raises(ValidationError):
            FinancialAssumptions(**self._valid(risk_free_rate=0.6))

    def test_market_return_below_risk_free_rejected(self) -> None:
        with pytest.raises(ValidationError):
            FinancialAssumptions(**self._valid(market_return=0.01))

    def test_terminal_growth_above_market_return_rejected(self) -> None:
        with pytest.raises(ValidationError):
            FinancialAssumptions(**self._valid(terminal_growth=0.15))

    def test_percentage_style_value_rejected(self) -> None:
        with pytest.raises(ValidationError):
            FinancialAssumptions(**self._valid(risk_free_rate=4.25))

    def test_projection_years_bounds(self) -> None:
        with pytest.raises(ValidationError):
            FinancialAssumptions(**self._valid(projection_years=0))
        with pytest.raises(ValidationError):
            FinancialAssumptions(**self._valid(projection_years=31))
        ok = FinancialAssumptions(**self._valid(projection_years=10))
        assert ok.projection_years == 10

    def test_model_is_frozen(self) -> None:
        a = FinancialAssumptions(**self._valid())
        with pytest.raises(ValidationError):
            a.risk_free_rate = 0.09

    def test_equity_risk_premium_derived(self) -> None:
        a = FinancialAssumptions(**self._valid())
        assert a.equity_risk_premium == pytest.approx(a.market_return - a.risk_free_rate)


class TestDefaultsAndFactory:
    def test_factory_uses_defaults(self) -> None:
        a = get_financial_assumptions()
        assert a.risk_free_rate == DEFAULT_RISK_FREE_RATE
        assert a.market_return == DEFAULT_MARKET_RETURN
        assert a.cost_of_debt == DEFAULT_COST_OF_DEBT
        assert a.tax_rate == DEFAULT_TAX_RATE
        assert a.terminal_growth == DEFAULT_TERMINAL_GROWTH
        assert a.projection_years == DEFAULT_PROJECTION_YEARS
        assert a.source == "configured"
        assert a.as_of == date.today()
        assert a.is_assumption is True

    def test_factory_reflects_settings(self) -> None:
        from app.core.config import Settings

        s = Settings(risk_free_rate=0.05, market_return=0.11)
        a = get_financial_assumptions(s)
        assert a.risk_free_rate == 0.05
        assert a.market_return == 0.11
        assert a.cost_of_debt == DEFAULT_COST_OF_DEBT


class TestRequestOverrides:
    def _base(self) -> FinancialAssumptions:
        return get_financial_assumptions()

    def test_partial_override(self) -> None:
        b = with_request_overrides(self._base(), risk_free_rate=0.05)
        assert b.risk_free_rate == 0.05
        assert b.market_return == DEFAULT_MARKET_RETURN
        assert b.source == "request"
        assert b.as_of == date.today()

    def test_no_override_keeps_base_values(self) -> None:
        base = self._base()
        b = with_request_overrides(base)
        assert b.risk_free_rate == base.risk_free_rate
        assert b.source == "request"

    def test_invalid_override_rejected(self) -> None:
        with pytest.raises(ValidationError):
            with_request_overrides(self._base(), risk_free_rate=9.9)

    def test_override_validated_against_base(self) -> None:
        with pytest.raises(ValidationError):
            with_request_overrides(self._base(), market_return=0.01)
