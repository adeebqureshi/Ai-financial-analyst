from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.config import Settings, get_settings


class FinancialAssumptions(BaseModel):
    model_config = ConfigDict(frozen=True)
    risk_free_rate: float = Field(
        ...,
        ge=0.0,
        le=0.5,
        description="Annual risk-free rate as a decimal (e.g. 0.0425 = 4.25%).",
    )
    market_return: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Expected annual market return as a decimal (e.g. 0.10 = 10%).",
    )
    cost_of_debt: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Pre-tax cost of debt as a decimal (e.g. 0.05 = 5%).",
    )
    tax_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Effective tax rate as a decimal (e.g. 0.21 = 21%).",
    )
    terminal_growth: float = Field(
        ...,
        ge=0.0,
        le=0.2,
        description="Perpetual terminal growth rate as a decimal (e.g. 0.03 = 3%).",
    )
    projection_years: int = Field(
        ...,
        ge=1,
        le=30,
        description="DCF projection horizon in whole years.",
    )
    source: str = Field(
        default="default",
        description="Provenance: 'default', 'configured', or 'request'.",
    )
    as_of: date | None = Field(
        default=None,
        description="Date the assumptions were set/validated.",
    )
    is_assumption: bool = Field(
        default=True,
        description="Always True; distinguishes assumptions from live market data.",
    )

    @field_validator("market_return")
    @classmethod
    def market_return_exceeds_risk_free(cls, v: float, info) -> float:
        rfr = info.data.get("risk_free_rate")
        if rfr is not None and v < rfr:
            raise ValueError(f"market_return must be >= risk_free_rate (got {v} < {rfr}).")
        return v

    @field_validator("terminal_growth")
    @classmethod
    def terminal_growth_below_market_return(cls, v: float, info) -> float:
        mr = info.data.get("market_return")
        if mr is not None and v >= mr:
            raise ValueError(
                f"terminal_growth must be strictly below market_return (got {v} >= {mr})."
            )
        return v

    @property
    def equity_risk_premium(self) -> float:
        return self.market_return - self.risk_free_rate


DEFAULT_RISK_FREE_RATE = 0.0425
DEFAULT_MARKET_RETURN = 0.10
DEFAULT_COST_OF_DEBT = 0.05
DEFAULT_TAX_RATE = 0.21
DEFAULT_TERMINAL_GROWTH = 0.03
DEFAULT_PROJECTION_YEARS = 5


def get_financial_assumptions(settings: Settings | None = None) -> FinancialAssumptions:
    settings = settings or get_settings()
    today = date.today()
    return FinancialAssumptions(
        risk_free_rate=settings.risk_free_rate,
        market_return=settings.market_return,
        cost_of_debt=settings.cost_of_debt,
        tax_rate=settings.tax_rate,
        terminal_growth=settings.terminal_growth,
        projection_years=settings.projection_years,
        source="configured",
        as_of=today,
    )


def with_request_overrides(
    base: FinancialAssumptions,
    *,
    risk_free_rate: float | None = None,
    market_return: float | None = None,
    cost_of_debt: float | None = None,
    tax_rate: float | None = None,
    terminal_growth: float | None = None,
    projection_years: int | None = None,
) -> FinancialAssumptions:
    today = date.today()
    values = base.model_dump()
    values.update(
        {
            key: val
            for key, val in {
                "risk_free_rate": risk_free_rate,
                "market_return": market_return,
                "cost_of_debt": cost_of_debt,
                "tax_rate": tax_rate,
                "terminal_growth": terminal_growth,
                "projection_years": projection_years,
            }.items()
            if val is not None
        }
    )
    values["source"] = "request"
    values["as_of"] = today
    return FinancialAssumptions(**values)
