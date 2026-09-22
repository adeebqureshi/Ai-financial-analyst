from __future__ import annotations
from datetime import date, datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.analysis import FinancialStatementInput
class MarketDataResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    ticker: str = Field(..., description="Stock ticker symbol.")
    exchange: str | None = Field(default=None, description="Listing exchange (NASDAQ, NYSE, AMEX, OTHER).")
    current_price: float | None = Field(
        default=None,
        ge=0,
        description=(
            "Current market price per share ($), or null when the price is "
            "genuinely unavailable (provider failure / no data). Never a "
            "fabricated 0.0."
        ),
    )
    currency: str = Field(default="USD", description="Quote currency.")
    market_cap: float | None = Field(default=None, ge=0, description="Market capitalization ($).")
    volume: int | None = Field(default=None, ge=0, description="Trading volume.")
    beta: float | None = Field(default=None, description="Stock beta.")
    pe_ratio: float | None = Field(default=None, ge=0, description="Trailing P/E ratio.")
    eps: float | None = Field(default=None, description="Trailing earnings per share ($).")
    dividend_yield: float | None = Field(default=None, ge=0, description="Dividend yield (0.0-1.0).")
    week_52_high: float | None = Field(default=None, ge=0, description="52-week high ($).")
    week_52_low: float | None = Field(default=None, ge=0, description="52-week low ($).")
    price_available: bool = Field(
        default=False,
        description=(
            "False when the market price is unavailable (provider failure, "
            "unknown ticker, or stale outage); clients must not treat "
            "current_price as a real value in that case."
        ),
    )
    provider: str | None = Field(
        default=None,
        description="Market-data provider that supplied the quote (e.g. 'yahoo', 'fmp').",
    )
    as_of: datetime | None = Field(
        default=None,
        description="Provider quote timestamp when available.",
    )
    cached: bool = Field(
        default=False,
        description="True when the quote was served from the market-data cache.",
    )
    stale: bool = Field(
        default=False,
        description="True when the quote exceeds the normal freshness window.",
    )
class ValuationResultData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    intrinsic_value: float = Field(..., description="Estimated intrinsic value per share ($).")
    upside: float = Field(..., description="Upside percentage.")
    recommendation: str = Field(..., description="Investment recommendation (STRONG BUY/BUY/HOLD/SELL).")
    current_price: float | None = Field(
        default=None,
        ge=0,
        description="Current market price per share ($); null when unavailable.",
    )
    discount_rate: float = Field(..., description="WACC discount rate used in the DCF.")
    assumptions_source: str | None = Field(
        default=None,
        description=(
            "Where the valuation inputs came from: 'default' (built-in "
            "assumptions), 'configured' (deployment settings), or 'request' "
            "(client-supplied parameters)."
        ),
    )
    assumptions_as_of: date | None = Field(
        default=None,
        description="Date the valuation assumptions were set/validated.",
    )
    risk_free_rate: float | None = Field(
        default=None,
        ge=0,
        description="Risk-free rate used (decimal). An assumption, not live data.",
    )
    market_return: float | None = Field(
        default=None,
        ge=0,
        description="Expected market return used (decimal). An assumption, not live data.",
    )
    cost_of_debt: float | None = Field(
        default=None,
        ge=0,
        description="Pre-tax cost of debt used (decimal). An assumption, not live data.",
    )
class HealthScoreData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    score: int = Field(..., ge=0, le=100, description="Composite health score (0-100).")
    rating: str = Field(..., description="Health rating (EXCELLENT/GOOD/FAIR/POOR).")
    piotroski_score: int = Field(..., ge=0, le=9, description="Piotroski F-Score (0-9).")
    altman_score: float = Field(..., description="Altman Z-Score.")
    beneish_score: float = Field(..., description="Beneish M-Score.")
class CompanyData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    ticker: str = Field(..., description="Ticker symbol.")
    name: str = Field(..., description="Company name.")
    sector: str | None = Field(default=None, description="Sector classification.")
    industry: str | None = Field(default=None, description="Industry classification.")
    market_cap: float | None = Field(default=None, description="Market capitalization ($).")
    description: str | None = Field(default=None, description="Short company description.")
class SearchHitData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(..., description="Chunk identifier.")
    text: str = Field(..., description="Retrieved text chunk.")
    score: float = Field(..., description="Relevance score.")
    ticker: str | None = Field(default=None, description="Associated ticker.")
    filing_type: str | None = Field(default=None, description="Filing type (10-K, 10-Q, etc.).")
    filing_date: date | None = Field(default=None, description="Filing date.")
    section: str | None = Field(default=None, description="Document section.")
    source: str | None = Field(default=None, description="Source URL or identifier.")
    document_id: str | None = Field(default=None, description="Document this chunk belongs to.")
    filename: str | None = Field(default=None, description="Uploaded filename.")
    page: int | None = Field(default=None, description="Page number within the document.")
    chunk_id: str | None = Field(default=None, description="Stable chunk identifier.")
class SearchResultData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    query: str = Field(..., description="Original query.")
    hits: list[SearchHitData] = Field(default_factory=list, description="List of retrieval hits.")
    total: int = Field(..., ge=0, description="Number of hits returned.")
    retrieval_time_ms: float = Field(..., ge=0, description="Retrieval latency (ms).")
class FinancialRatiosData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    debt_to_equity: float = Field(..., description="Debt-to-equity ratio.")
    return_on_assets: float = Field(..., description="Return on assets (ROA).")
    return_on_equity: float = Field(..., description="Return on equity (ROE).")
    operating_margin: float = Field(..., description="Operating margin.")
    net_margin: float = Field(..., description="Net margin.")
class RiskAssessmentData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    health_score: int = Field(..., ge=0, le=100, description="Composite health score (0-100).")
    health_rating: str = Field(..., description="Health rating.")
    piotroski: dict[str, Any] = Field(..., description="Piotroski interpretation.")
    altman: dict[str, Any] = Field(..., description="Altman Z-Score interpretation.")
    beneish: dict[str, Any] = Field(..., description="Beneish M-Score interpretation.")
    risk_level: str = Field(..., description="Overall risk level (LOW/MEDIUM/HIGH).")
class ReportData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    ticker: str = Field(..., description="Ticker symbol.")
    title: str = Field(..., description="Report title.")
    content: str = Field(..., description="Markdown report content.")
    format: str = Field(default="markdown", description="Report format.")
class ChatResponseData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    message: str = Field(..., description="Assistant reply text.")
    ticker: str | None = Field(default=None, description="Optional ticker context.")
    model: str | None = Field(default=None, description="LLM model used.")
    sources: list[DocumentCitation] = Field(
        default_factory=list,
        description="Grounding citations for the answer.",
    )
    plan: list[str] = Field(
        default_factory=list,
        description="High-level execution steps the agent actually ran.",
    )
    tools_used: list[AgentToolExecutionData] = Field(
        default_factory=list,
        description="Tool-transparency metadata for the tools that ran.",
    )
class ChatSessionData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    session_id: str = Field(..., description="Client-supplied session identifier.")
    title: str | None = Field(default=None, description="Optional session title.")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary session metadata (JSON).",
    )
    created_at: datetime = Field(..., description="UTC creation timestamp.")
    updated_at: datetime = Field(..., description="UTC last-activity timestamp.")
class ChatMessageData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: int = Field(..., description="Database row identifier.")
    role: str = Field(..., description="Message role (user/assistant/system).")
    content: str = Field(..., description="Message text.")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary per-message metadata (JSON).",
    )
    created_at: datetime = Field(..., description="UTC storage timestamp.")
class ChatSessionListData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    sessions: list[ChatSessionData] = Field(
        default_factory=list,
        description="The current page of sessions.",
    )
    total: int = Field(default=0, ge=0, description="Total owned sessions.")
class ChatMessageListData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    messages: list[ChatMessageData] = Field(
        default_factory=list,
        description="The current page of messages.",
    )
    total: int = Field(default=0, ge=0, description="Total messages in the session.")
class DocumentCitation(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    document_id: str = Field(..., description="The uploaded document identifier.")
    filename: str = Field(..., description="The uploaded filename.")
    page: int | None = Field(default=None, description="Page number of the cited text.")
    chunk_id: str | None = Field(default=None, description="Stable chunk identifier.")
    score: float | None = Field(default=None, description="Relevance score of the cited chunk.")
class AgentToolExecutionData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    tool: str = Field(..., description="Tool name.")
    status: str = Field(..., description="Execution status (done/error/running/skipped).")
    detail: str | None = Field(default=None, description="Short human-readable summary.")
class DocumentData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    document_id: str = Field(..., description="Unique document identifier.")
    filename: str = Field(..., description="Original uploaded filename.")
    pages: int = Field(default=0, ge=0, description="Number of pages in the document.")
    chunks: int = Field(default=0, ge=0, description="Number of indexed chunks.")
    status: str = Field(default="indexed", description="Indexing status.")
    created_at: datetime | None = Field(default=None, description="Indexing timestamp.")
class DocumentListData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    documents: list[DocumentData] = Field(default_factory=list, description="Indexed document records.")
    total: int = Field(default=0, ge=0, description="Number of documents returned.")
class AnalyzeResponseData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    ticker: str = Field(..., description="Ticker symbol.")
    query: str = Field(..., description="Original analysis query.")
    company: CompanyData = Field(..., description="Company profile.")
    market: MarketDataResponse = Field(..., description="Live market snapshot.")
    statement: FinancialStatementInput = Field(..., description="Financial statement data used for the analysis.")
    valuation: ValuationResultData = Field(..., description="Valuation result.")
    health: HealthScoreData = Field(..., description="Financial health score.")
    recommendation: str = Field(..., description="Overall investment recommendation.")
class ValuationResponseData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    ticker: str | None = Field(default=None, description="Optional ticker symbol.")
    valuation: ValuationResultData = Field(..., description="Valuation result.")
class IntrinsicValueResponseData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    intrinsic_value: float = Field(..., description="Intrinsic value per share ($).")
    current_price: float = Field(..., description="Current market price per share ($).")
    upside: float = Field(..., description="Upside percentage.")
class CompareItemData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    ticker: str = Field(..., description="Ticker symbol.")
    name: str | None = Field(default=None, description="Optional company name.")
    intrinsic_value: float = Field(..., description="Intrinsic value per share ($).")
    upside: float = Field(..., description="Upside percentage.")
    recommendation: str = Field(..., description="Recommendation string.")
    health_score: int | None = Field(default=None, description="Optional health score.")
class CompareResponseData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    results: list[CompareItemData] = Field(default_factory=list, description="Per-ticker comparison results.")
    best: str = Field(..., description="Best ticker by upside.")
class ScreenItemData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    ticker: str = Field(..., description="Ticker symbol.")
    name: str | None = Field(default=None, description="Optional company name.")
    piotroski_score: int = Field(..., ge=0, le=9, description="Piotroski F-Score.")
    altman_score: float = Field(..., description="Altman Z-Score.")
    beneish_score: float = Field(..., description="Beneish M-Score.")
    health_score: int = Field(..., ge=0, le=100, description="Health score.")
    health_rating: str = Field(..., description="Health rating.")
    intrinsic_value: float = Field(..., description="Intrinsic value per share ($).")
    upside: float = Field(..., description="Upside percentage.")
    recommendation: str = Field(..., description="Recommendation string.")
class ScreenResponseData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    results: list[ScreenItemData] = Field(default_factory=list, description="Screening results.")
    total: int = Field(..., ge=0, description="Number of results returned.")