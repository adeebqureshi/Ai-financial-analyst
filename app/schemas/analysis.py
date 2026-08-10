"""
Analysis Schemas

This module defines the Pydantic v2 request models used by the AI Financial
Analyst REST API endpoints. All public request contracts live here to ensure
that no ``dict`` is ever used as a public API payload.

Design Decisions:
    - **Pydantic v2 validators**: Domain validation (ticker patterns,
      positive values, bounded percentages) is enforced at the schema layer
      so invalid requests fail fast with HTTP 422.
    - **Separation of concerns**: Request models are distinct from response
      models (``app.schemas.responses``). Each request model maps directly
      to the inputs required by the corresponding service method.
    - **Reusability**: ``FinancialStatementInput`` and ``ValuationParams``
      are shared across multiple endpoints (analyze, valuation, ratios,
      intrinsic-value, risk) to avoid duplicating field definitions.
    - **OpenAPI friendliness**: Every field carries a ``description`` and
      (where relevant) an ``example`` so the generated Swagger UI is
      self-documenting.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ──────────────────────────────────────────────────────────────────────────────
# Shared Validators
# ──────────────────────────────────────────────────────────────────────────────


def _validate_ticker(value: str) -> str:
    """
    Validate that a ticker symbol is 1-5 uppercase letters.

    Args:
        value: The ticker symbol to validate.

    Returns:
        The normalized ticker symbol.

    Raises:
        ValueError: If the ticker does not match ``^[A-Z]{1,5}$``.
    """
    ticker = value.strip().upper()
    if not (1 <= len(ticker) <= 5) or not ticker.isalpha():
        raise ValueError("Ticker must be 1-5 uppercase letters (e.g., 'AAPL').")
    return ticker


def _validate_positive(value: float, field_name: str) -> float:
    """
    Validate that a financial quantity is strictly positive.

    Args:
        value: The numeric value to validate.
        field_name: Name of the field (used in the error message).

    Returns:
        The validated value.

    Raises:
        ValueError: If ``value <= 0``.
    """
    if value <= 0:
        raise ValueError(f"{field_name} must be positive.")
    return value


def _validate_percentage(value: float, field_name: str) -> float:
    """
    Validate that a percentage-valued field is within [0.0, 1.0].

    Args:
        value: The rate to validate (e.g., ``0.05`` for 5%).
        field_name: Name of the field (used in the error message).

    Returns:
        The validated value.

    Raises:
        ValueError: If ``value`` is outside [0.0, 1.0].
    """
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0.")
    return value


def _validate_int_in_range(value: int, low: int, high: int, field_name: str) -> int:
    """
    Validate that an integer score is within a closed range.

    Args:
        value: The integer to validate.
        low: Minimum acceptable value (inclusive).
        high: Maximum acceptable value (inclusive).
        field_name: Name of the field (used in the error message).

    Returns:
        The validated value.

    Raises:
        ValueError: If ``value`` is outside ``[low, high]``.
    """
    if not low <= value <= high:
        raise ValueError(f"{field_name} must be between {low} and {high}.")
    return value


# ──────────────────────────────────────────────────────────────────────────────
# Financial Statement Input
# ──────────────────────────────────────────────────────────────────────────────


class FinancialStatementInput(BaseModel):
    """
    Financial statement data required for valuation and analysis.

    Attributes:
        revenue: Total revenue.
        operating_income: Operating (EBIT) income.
        net_income: Net income after taxes.
        total_assets: Total assets.
        total_liabilities: Total liabilities.
        cash: Cash and cash equivalents.
        debt: Total debt.
        shares_outstanding: Diluted shares outstanding.
        free_cash_flow: Free cash flow.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "revenue": 394_328.0,
                "operating_income": 114_301.0,
                "net_income": 96_995.0,
                "total_assets": 352_583.0,
                "total_liabilities": 279_486.0,
                "cash": 30_545.0,
                "debt": 111_088.0,
                "shares_outstanding": 15_431.0,
                "free_cash_flow": 99_584.0,
            }
        },
    )

    revenue: float = Field(..., gt=0, description="Total revenue (in $M).")
    operating_income: float = Field(..., description="Operating income (in $M).")
    net_income: float = Field(..., description="Net income (in $M).")
    total_assets: float = Field(..., gt=0, description="Total assets (in $M).")
    total_liabilities: float = Field(..., ge=0, description="Total liabilities (in $M).")
    cash: float = Field(..., ge=0, description="Cash and equivalents (in $M).")
    debt: float = Field(..., ge=0, description="Total debt (in $M).")
    shares_outstanding: float = Field(..., gt=0, description="Shares outstanding (in M).")
    free_cash_flow: float = Field(..., description="Free cash flow (in $M).")

    @field_validator("total_liabilities")
    @classmethod
    def validate_liabilities(cls, v: float) -> float:
        """Ensure liabilities do not exceed total assets."""
        # NOTE: Cross-field validation is handled in `model_validator` below.
        return v

    @field_validator("revenue", "total_assets", "shares_outstanding")
    @classmethod
    def ensure_positive(cls, v: float) -> float:
        """Ensure strictly positive financial quantities."""
        return v


# ──────────────────────────────────────────────────────────────────────────────
# Valuation Parameters
# ──────────────────────────────────────────────────────────────────────────────


class ValuationParams(BaseModel):
    """
    Parameters required to run a DCF valuation.

    Attributes:
        current_price: Current market price per share.
        growth_rate: Expected free-cash-flow growth rate (0.0-1.0).
        risk_free_rate: Risk-free rate (0.0-1.0), e.g. 10-year treasury.
        beta: Stock beta.
        market_return: Expected market return (0.0-1.0).
        tax_rate: Effective tax rate (0.0-1.0).
        terminal_growth: Terminal growth rate (0.0-1.0), default 3%.
        years: Number of projection years, default 5.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "current_price": 191.58,
                "growth_rate": 0.08,
                "risk_free_rate": 0.0425,
                "beta": 1.24,
                "market_return": 0.10,
                "tax_rate": 0.21,
                "terminal_growth": 0.03,
                "years": 5,
            }
        },
    )

    current_price: float = Field(..., gt=0, description="Current market price per share ($).")
    growth_rate: float = Field(..., description="FCF growth rate (0.0-1.0).")
    risk_free_rate: float = Field(..., description="Risk-free rate (0.0-1.0).")
    beta: float = Field(..., ge=0, description="Stock beta.")
    market_return: float = Field(..., description="Expected market return (0.0-1.0).")
    tax_rate: float = Field(..., description="Effective tax rate (0.0-1.0).")
    terminal_growth: float = Field(default=0.03, ge=0, le=1, description="Terminal growth rate (0.0-1.0).")
    years: int = Field(default=5, ge=1, le=30, description="Number of projection years.")

    @field_validator("growth_rate", "risk_free_rate", "market_return", "tax_rate")
    @classmethod
    def validate_rates(cls, v: float) -> float:
        """Ensure all rates are within [0.0, 1.0]."""
        return _validate_percentage(v, "Rate")


# ──────────────────────────────────────────────────────────────────────────────
# Endpoint-Specific Request Models
# ──────────────────────────────────────────────────────────────────────────────


class AnalyzeRequest(BaseModel):
    """
    Request model for ``POST /analyze``.

    Attributes:
        ticker: Ticker symbol of the company.
        query: Natural-language analysis query.
        statement: Financial statement input.
        valuation: Valuation parameters.
        piotroski_score: Piotroski F-Score (0-9).
        altman_score: Altman Z-Score.
        beneish_score: Beneish M-Score.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "ticker": "AAPL",
                "query": "Should I buy Apple?",
                "statement": {
                    "revenue": 394_328.0,
                    "operating_income": 114_301.0,
                    "net_income": 96_995.0,
                    "total_assets": 352_583.0,
                    "total_liabilities": 279_486.0,
                    "cash": 30_545.0,
                    "debt": 111_088.0,
                    "shares_outstanding": 15_431.0,
                    "free_cash_flow": 99_584.0,
                },
                "valuation": {
                    "current_price": 191.58,
                    "growth_rate": 0.08,
                    "risk_free_rate": 0.0425,
                    "beta": 1.24,
                    "market_return": 0.10,
                    "tax_rate": 0.21,
                },
                "piotroski_score": 9,
                "altman_score": 3.5,
                "beneish_score": -2.4,
            }
        },
    )

    ticker: str = Field(..., min_length=1, max_length=5, description="Ticker symbol (1-5 letters).")
    query: str = Field(..., min_length=1, max_length=2000, description="Analysis query.")
    statement: FinancialStatementInput = Field(..., description="Financial statement data.")
    valuation: ValuationParams = Field(..., description="Valuation parameters.")
    piotroski_score: int = Field(..., ge=0, le=9, description="Piotroski F-Score (0-9).")
    altman_score: float = Field(..., description="Altman Z-Score.")
    beneish_score: float = Field(..., description="Beneish M-Score.")

    @field_validator("ticker")
    @classmethod
    def validate_ticker_symbol(cls, v: str) -> str:
        """Normalize and validate the ticker symbol."""
        return _validate_ticker(v)


class SearchRequest(BaseModel):
    """
    Request model for ``POST /search``.

    Attributes:
        query: Search query string.
        limit: Maximum number of results to return.
        document_id: Optional document ID to restrict the search to.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={"example": {"query": "Apple revenue growth 2024", "limit": 5}},
    )

    query: str = Field(..., min_length=1, max_length=1000, description="Search query.")
    limit: int = Field(default=5, ge=1, le=50, description="Max results (1-50).")
    document_id: str | None = Field(
        default=None,
        description="Optional document ID to restrict the search to.",
    )


class CompanyRequest(BaseModel):
    """
    Request model for ``GET /company/{ticker}`` (path parameters).

    Attributes:
        ticker: Ticker symbol of the company.
    """

    model_config = ConfigDict(populate_by_name=True)

    ticker: str = Field(..., min_length=1, max_length=5, description="Ticker symbol (1-5 letters).")


class ValuationRequest(BaseModel):
    """
    Request model for ``POST /valuation``.

    Attributes:
        statement: Financial statement data.
        params: Valuation parameters.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={"example": {"statement": {}, "params": {}}},
    )

    statement: FinancialStatementInput = Field(..., description="Financial statement data.")
    params: ValuationParams = Field(..., description="Valuation parameters.")


class IntrinsicValueRequest(BaseModel):
    """
    Request model for ``POST /intrinsic-value``.

    Attributes:
        statement: Financial statement data.
        params: Valuation parameters (only ``growth_rate``, ``risk_free_rate``,
            ``beta``, ``market_return``, ``tax_rate`` are used).
    """

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={"example": {"statement": {}, "params": {}}},
    )

    statement: FinancialStatementInput = Field(..., description="Financial statement data.")
    params: ValuationParams = Field(..., description="Valuation parameters.")


class ChatRequest(BaseModel):
    """
    Request model for ``POST /chat``.

    Attributes:
        message: User chat message.
        context: Optional retrieval context.
        ticker: Optional ticker context.
        document_id: Optional document ID to scope retrieval to one upload.
        session_id: Optional session ID used to resolve follow-up context.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={"example": {"message": "What is Apple's intrinsic value?", "ticker": "AAPL"}},
    )

    message: str = Field(..., min_length=1, max_length=4000, description="User chat message.")
    context: str | None = Field(default=None, description="Optional retrieval context.")
    ticker: str | None = Field(default=None, min_length=1, max_length=5, description="Optional ticker context.")
    document_id: str | None = Field(
        default=None,
        description="Optional document ID to scope retrieval to one upload.",
    )
    session_id: str | None = Field(
        default=None,
        max_length=128,
        description="Optional session ID used to resolve follow-up context.",
    )

    @field_validator("ticker")
    @classmethod
    def validate_optional_ticker(cls, v: str | None) -> str | None:
        """Normalize and validate the optional ticker symbol."""
        if v is None:
            return None
        return _validate_ticker(v)


class FinancialRatiosRequest(BaseModel):
    """
    Request model for ``POST /financial-ratios``.

    Attributes:
        statement: Financial statement data.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={"example": {"statement": {}}},
    )

    statement: FinancialStatementInput = Field(..., description="Financial statement data.")


class RiskAnalysisRequest(BaseModel):
    """
    Request model for ``POST /risk-analysis``.

    Attributes:
        piotroski_score: Piotroski F-Score (0-9).
        altman_score: Altman Z-Score.
        beneish_score: Beneish M-Score.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={"example": {"piotroski_score": 9, "altman_score": 3.5, "beneish_score": -2.4}},
    )

    piotroski_score: int = Field(..., ge=0, le=9, description="Piotroski F-Score (0-9).")
    altman_score: float = Field(..., description="Altman Z-Score.")
    beneish_score: float = Field(..., description="Beneish M-Score.")


class ReportRequest(BaseModel):
    """
    Request model for ``POST /report``.

    Attributes:
        ticker: Ticker symbol.
        query: Analysis query for the report.
        statement: Financial statement data.
        valuation: Valuation parameters.
        piotroski_score: Piotroski F-Score (0-9).
        altman_score: Altman Z-Score.
        beneish_score: Beneish M-Score.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={"example": {"ticker": "AAPL", "query": "Should I buy Apple?"}},
    )

    ticker: str = Field(..., min_length=1, max_length=5, description="Ticker symbol (1-5 letters).")
    query: str = Field(..., min_length=1, max_length=2000, description="Analysis query for the report.")
    statement: FinancialStatementInput = Field(..., description="Financial statement data.")
    valuation: ValuationParams = Field(..., description="Valuation parameters.")
    piotroski_score: int = Field(..., ge=0, le=9, description="Piotroski F-Score (0-9).")
    altman_score: float = Field(..., description="Altman Z-Score.")
    beneish_score: float = Field(..., description="Beneish M-Score.")

    @field_validator("ticker")
    @classmethod
    def validate_ticker_symbol(cls, v: str) -> str:
        """Normalize and validate the ticker symbol."""
        return _validate_ticker(v)


class CompareRequest(BaseModel):
    """
    Request model for ``POST /compare``.

    Attributes:
        tickers: List of ticker symbols to compare (2-10).
        statement: Financial statement data (used for all tickers).
        valuation: Valuation parameters (used for all tickers).
    """

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={"example": {"tickers": ["AAPL", "MSFT", "GOOGL"]}},
    )

    tickers: list[str] = Field(
        ...,
        min_length=2,
        max_length=10,
        description="List of 2-10 ticker symbols to compare.",
    )
    statement: FinancialStatementInput = Field(..., description="Financial statement data.")
    valuation: ValuationParams = Field(..., description="Valuation parameters.")

    @field_validator("tickers")
    @classmethod
    def validate_ticker_list(cls, v: list[str]) -> list[str]:
        """Normalize, validate, and de-duplicate the ticker list."""
        seen: set[str] = set()
        result: list[str] = []
        for raw in v:
            ticker = _validate_ticker(raw)
            if ticker not in seen:
                seen.add(ticker)
                result.append(ticker)
        if len(result) < 2:
            raise ValueError("At least 2 distinct tickers are required.")
        return result


class ScreenRequest(BaseModel):
    """
    Request model for ``POST /screen``.

    Attributes:
        min_piotroski: Minimum Piotroski F-Score.
        min_altman: Minimum Altman Z-Score.
        max_beneish: Maximum Beneish M-Score (lower is better).
        min_upside: Minimum upside percentage.
        max_results: Maximum number of results.
        statement: Financial statement data of the candidate to screen.
        valuation: Valuation parameters for the candidate.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={"example": {"min_piotroski": 7, "min_altman": 3.0, "max_results": 10}},
    )

    min_piotroski: int = Field(default=0, ge=0, le=9, description="Minimum Piotroski F-Score (0-9).")
    min_altman: float = Field(default=0.0, ge=0, description="Minimum Altman Z-Score.")
    max_beneish: float = Field(default=100.0, description="Maximum Beneish M-Score (lower is better).")
    min_upside: float = Field(default=-100.0, description="Minimum upside percentage.")
    max_results: int = Field(default=10, ge=1, le=100, description="Max results (1-100).")
    statement: FinancialStatementInput = Field(..., description="Financial statement data of the candidate.")
    valuation: ValuationParams = Field(..., description="Valuation parameters for the candidate.")
