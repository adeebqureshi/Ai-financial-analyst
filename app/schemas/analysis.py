from __future__ import annotations
from datetime import date
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.utils.tickers import normalize_ticker
def _validate_ticker(value: str) -> str:
    return normalize_ticker(value)
def _validate_positive(value: float, field_name: str) -> float:
    if value <= 0:
        raise ValueError(f"{field_name} must be positive.")
    return value
def _validate_percentage(value: float, field_name: str) -> float:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0.")
    return value
def _validate_int_in_range(value: int, low: int, high: int, field_name: str) -> int:
    if not low <= value <= high:
        raise ValueError(f"{field_name} must be between {low} and {high}.")
    return value
class FinancialStatementInput(BaseModel):
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
        return v
    @field_validator("revenue", "total_assets", "shares_outstanding")
    @classmethod
    def ensure_positive(cls, v: float) -> float:
        return v
class ValuationParams(BaseModel):
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
    current_price: float | None = Field(
        default=None,
        ge=0,
        description="Current market price per share ($). Null/0 if unavailable.",
    )
    growth_rate: float = Field(..., description="FCF growth rate (0.0-1.0).")
    risk_free_rate: float = Field(..., description="Risk-free rate (0.0-1.0).")
    beta: float = Field(..., ge=0, description="Stock beta.")
    market_return: float = Field(..., description="Expected market return (0.0-1.0).")
    tax_rate: float = Field(..., description="Effective tax rate (0.0-1.0).")
    cost_of_debt: float = Field(default=0.05, ge=0, le=1, description="Pre-tax cost of debt (0.0-1.0).")
    terminal_growth: float = Field(default=0.03, ge=0, le=1, description="Terminal growth rate (0.0-1.0).")
    years: int = Field(default=5, ge=1, le=30, description="Number of projection years.")
    @field_validator("growth_rate", "risk_free_rate", "market_return", "tax_rate", "cost_of_debt")
    @classmethod
    def validate_rates(cls, v: float) -> float:
        return _validate_percentage(v, "Rate")
class AnalyzeRequest(BaseModel):
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
        return _validate_ticker(v)
class SearchRequest(BaseModel):
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
    as_of_date: date | None = Field(
        default=None,
        description=(
            "Optional historical as-of date (YYYY-MM-DD). When provided, "
            "retrieval excludes information the system did not know by that "
            "date, preventing look-ahead bias."
        ),
    )
class CompanyRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    ticker: str = Field(..., min_length=1, max_length=5, description="Ticker symbol (1-5 letters).")
class ValuationRequest(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={"example": {"statement": {}, "params": {}}},
    )
    statement: FinancialStatementInput = Field(..., description="Financial statement data.")
    params: ValuationParams = Field(..., description="Valuation parameters.")
class IntrinsicValueRequest(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={"example": {"statement": {}, "params": {}}},
    )
    statement: FinancialStatementInput = Field(..., description="Financial statement data.")
    params: ValuationParams = Field(..., description="Valuation parameters.")
class ChatRequest(BaseModel):
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
    as_of_date: date | None = Field(
        default=None,
        description=(
            "Optional historical as-of date (YYYY-MM-DD). When provided, "
            "document retrieval excludes information the system did not "
            "know by that date."
        ),
    )
    @field_validator("ticker")
    @classmethod
    def validate_optional_ticker(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return _validate_ticker(v)
class FinancialRatiosRequest(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={"example": {"statement": {}}},
    )
    statement: FinancialStatementInput = Field(..., description="Financial statement data.")
class RiskAnalysisRequest(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={"example": {"piotroski_score": 9, "altman_score": 3.5, "beneish_score": -2.4}},
    )
    piotroski_score: int = Field(..., ge=0, le=9, description="Piotroski F-Score (0-9).")
    altman_score: float = Field(..., description="Altman Z-Score.")
    beneish_score: float = Field(..., description="Beneish M-Score.")
class ReportRequest(BaseModel):
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
        return _validate_ticker(v)
class CompareRequest(BaseModel):
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