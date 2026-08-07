"""
Response Schemas

This module defines the Pydantic v2 response models used by the AI Financial
Analyst REST API endpoints. Every response model is a typed DTO — never a
``dict`` — ensuring a stable public API contract.

Design Decisions:
    - **Typed DTOs over dicts**: Each endpoint returns a dedicated response
      model, making the OpenAPI schema self-documenting and type-safe.
    - **Nested responses**: ``ValuationResultData`` and ``HealthScoreData``
      are reused by multiple endpoint responses to avoid duplication.
    - **Consistent naming**: Response models mirror the request models in
      ``app.schemas.analysis`` and the domain models in ``app.financial``
      and ``app.retrieval``.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ──────────────────────────────────────────────────────────────────────────────
# Valuation / Analysis Sub-Responses
# ──────────────────────────────────────────────────────────────────────────────


class ValuationResultData(BaseModel):
    """
    Valuation result payload.

    Attributes:
        intrinsic_value: Estimated intrinsic value per share.
        upside: Upside percentage (positive = undervalued).
        recommendation: BUY/SELL/HOLD recommendation.
        current_price: Current market price per share.
        discount_rate: Weighted average cost of capital used.
    """

    model_config = ConfigDict(populate_by_name=True)

    intrinsic_value: float = Field(..., description="Estimated intrinsic value per share ($).")
    upside: float = Field(..., description="Upside percentage.")
    recommendation: str = Field(..., description="Investment recommendation (STRONG BUY/BUY/HOLD/SELL).")
    current_price: float = Field(..., description="Current market price per share ($).")
    discount_rate: float = Field(..., description="WACC discount rate used in the DCF.")


class HealthScoreData(BaseModel):
    """
    Financial health score payload.

    Attributes:
        score: Composite health score (0-100).
        rating: Rating (EXCELLENT/GOOD/FAIR/POOR).
        piotroski_score: Piotroski F-Score (0-9).
        altman_score: Altman Z-Score.
        beneish_score: Beneish M-Score.
    """

    model_config = ConfigDict(populate_by_name=True)

    score: int = Field(..., ge=0, le=100, description="Composite health score (0-100).")
    rating: str = Field(..., description="Health rating (EXCELLENT/GOOD/FAIR/POOR).")
    piotroski_score: int = Field(..., ge=0, le=9, description="Piotroski F-Score (0-9).")
    altman_score: float = Field(..., description="Altman Z-Score.")
    beneish_score: float = Field(..., description="Beneish M-Score.")


# ──────────────────────────────────────────────────────────────────────────────
# Company
# ──────────────────────────────────────────────────────────────────────────────


class CompanyData(BaseModel):
    """
    Company profile payload.

    Attributes:
        ticker: Ticker symbol.
        name: Company name.
        sector: Sector classification.
        industry: Industry classification.
        market_cap: Market capitalization.
        description: Short company description.
    """

    model_config = ConfigDict(populate_by_name=True)

    ticker: str = Field(..., description="Ticker symbol.")
    name: str = Field(..., description="Company name.")
    sector: str | None = Field(default=None, description="Sector classification.")
    industry: str | None = Field(default=None, description="Industry classification.")
    market_cap: float | None = Field(default=None, description="Market capitalization ($).")
    description: str | None = Field(default=None, description="Short company description.")


# ──────────────────────────────────────────────────────────────────────────────
# Search
# ──────────────────────────────────────────────────────────────────────────────


class SearchHitData(BaseModel):
    """
    Single retrieval hit payload.

    Attributes:
        id: Chunk identifier.
        text: Retrieved text chunk.
        score: Similarity/relevance score.
        ticker: Associated ticker.
        filing_type: Filing type (10-K, 10-Q, etc.).
        filing_date: Filing date.
        section: Document section.
        source: Source URL or identifier.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., description="Chunk identifier.")
    text: str = Field(..., description="Retrieved text chunk.")
    score: float = Field(..., description="Relevance score.")
    ticker: str | None = Field(default=None, description="Associated ticker.")
    filing_type: str | None = Field(default=None, description="Filing type (10-K, 10-Q, etc.).")
    filing_date: date | None = Field(default=None, description="Filing date.")
    section: str | None = Field(default=None, description="Document section.")
    source: str | None = Field(default=None, description="Source URL or identifier.")


class SearchResultData(BaseModel):
    """
    Search result payload.

    Attributes:
        query: Original query.
        hits: List of retrieval hits.
        total: Number of hits returned.
        retrieval_time_ms: Retrieval latency in milliseconds.
    """

    model_config = ConfigDict(populate_by_name=True)

    query: str = Field(..., description="Original query.")
    hits: list[SearchHitData] = Field(default_factory=list, description="List of retrieval hits.")
    total: int = Field(..., ge=0, description="Number of hits returned.")
    retrieval_time_ms: float = Field(..., ge=0, description="Retrieval latency (ms).")


# ──────────────────────────────────────────────────────────────────────────────
# Ratios
# ──────────────────────────────────────────────────────────────────────────────


class FinancialRatiosData(BaseModel):
    """
    Financial ratio payload.

    Attributes:
        debt_to_equity: Debt-to-equity ratio.
        return_on_assets: Return on assets (ROA).
        return_on_equity: Return on equity (ROE).
        operating_margin: Operating margin.
        net_margin: Net margin.
    """

    model_config = ConfigDict(populate_by_name=True)

    debt_to_equity: float = Field(..., description="Debt-to-equity ratio.")
    return_on_assets: float = Field(..., description="Return on assets (ROA).")
    return_on_equity: float = Field(..., description="Return on equity (ROE).")
    operating_margin: float = Field(..., description="Operating margin.")
    net_margin: float = Field(..., description="Net margin.")


# ──────────────────────────────────────────────────────────────────────────────
# Risk
# ──────────────────────────────────────────────────────────────────────────────


class RiskAssessmentData(BaseModel):
    """
    Risk assessment payload.

    Attributes:
        health_score: Composite health score.
        health_rating: Health rating.
        piotroski: Piotroski interpretation.
        altman: Altman Z-Score interpretation.
        beneish: Beneish M-Score interpretation.
        risk_level: Overall risk level (LOW/MEDIUM/HIGH).
    """

    model_config = ConfigDict(populate_by_name=True)

    health_score: int = Field(..., ge=0, le=100, description="Composite health score (0-100).")
    health_rating: str = Field(..., description="Health rating.")
    piotroski: dict[str, Any] = Field(..., description="Piotroski interpretation.")
    altman: dict[str, Any] = Field(..., description="Altman Z-Score interpretation.")
    beneish: dict[str, Any] = Field(..., description="Beneish M-Score interpretation.")
    risk_level: str = Field(..., description="Overall risk level (LOW/MEDIUM/HIGH).")


# ──────────────────────────────────────────────────────────────────────────────
# Report & Chat
# ──────────────────────────────────────────────────────────────────────────────


class ReportData(BaseModel):
    """
    Generated report payload.

    Attributes:
        ticker: Ticker symbol.
        title: Report title.
        content: Markdown report content.
        format: Report format (markdown).
    """

    model_config = ConfigDict(populate_by_name=True)

    ticker: str = Field(..., description="Ticker symbol.")
    title: str = Field(..., description="Report title.")
    content: str = Field(..., description="Markdown report content.")
    format: str = Field(default="markdown", description="Report format.")


class ChatResponseData(BaseModel):
    """
    Chat response payload.

    Attributes:
        message: Assistant reply text.
        ticker: Optional ticker context.
        model: LLM model used.
    """

    model_config = ConfigDict(populate_by_name=True)

    message: str = Field(..., description="Assistant reply text.")
    ticker: str | None = Field(default=None, description="Optional ticker context.")
    model: str | None = Field(default=None, description="LLM model used.")


# ──────────────────────────────────────────────────────────────────────────────
# Top-Level Endpoint Responses
# ──────────────────────────────────────────────────────────────────────────────


class AnalyzeResponseData(BaseModel):
    """
    Analyze endpoint response payload.

    Attributes:
        ticker: Ticker symbol.
        query: Original analysis query.
        company: Company profile.
        valuation: Valuation result.
        health: Financial health score.
        recommendation: Overall investment recommendation.
    """

    model_config = ConfigDict(populate_by_name=True)

    ticker: str = Field(..., description="Ticker symbol.")
    query: str = Field(..., description="Original analysis query.")
    company: CompanyData = Field(..., description="Company profile.")
    valuation: ValuationResultData = Field(..., description="Valuation result.")
    health: HealthScoreData = Field(..., description="Financial health score.")
    recommendation: str = Field(..., description="Overall investment recommendation.")


class ValuationResponseData(BaseModel):
    """
    Valuation endpoint response payload.

    Attributes:
        ticker: Optional ticker symbol.
        valuation: Valuation result.
    """

    model_config = ConfigDict(populate_by_name=True)

    ticker: str | None = Field(default=None, description="Optional ticker symbol.")
    valuation: ValuationResultData = Field(..., description="Valuation result.")


class IntrinsicValueResponseData(BaseModel):
    """
    Intrinsic value endpoint response payload.

    Attributes:
        intrinsic_value: Intrinsic value per share.
        current_price: Current market price per share.
        upside: Upside percentage.
    """

    model_config = ConfigDict(populate_by_name=True)

    intrinsic_value: float = Field(..., description="Intrinsic value per share ($).")
    current_price: float = Field(..., description="Current market price per share ($).")
    upside: float = Field(..., description="Upside percentage.")


class CompareItemData(BaseModel):
    """
    Single company comparison payload.

    Attributes:
        ticker: Ticker symbol.
        name: Optional company name.
        intrinsic_value: Intrinsic value per share.
        upside: Upside percentage.
        recommendation: Recommendation string.
        health_score: Optional health score.
    """

    model_config = ConfigDict(populate_by_name=True)

    ticker: str = Field(..., description="Ticker symbol.")
    name: str | None = Field(default=None, description="Optional company name.")
    intrinsic_value: float = Field(..., description="Intrinsic value per share ($).")
    upside: float = Field(..., description="Upside percentage.")
    recommendation: str = Field(..., description="Recommendation string.")
    health_score: int | None = Field(default=None, description="Optional health score.")


class CompareResponseData(BaseModel):
    """
    Compare endpoint response payload.

    Attributes:
        results: List of per-ticker comparisons.
        best: Best ticker by upside.
    """

    model_config = ConfigDict(populate_by_name=True)

    results: list[CompareItemData] = Field(default_factory=list, description="Per-ticker comparison results.")
    best: str = Field(..., description="Best ticker by upside.")


class ScreenItemData(BaseModel):
    """
    Single screening result payload.

    Attributes:
        ticker: Ticker symbol.
        name: Optional company name.
        piotroski_score: Piotroski F-Score.
        altman_score: Altman Z-Score.
        beneish_score: Beneish M-Score.
        health_score: Health score.
        health_rating: Health rating.
        intrinsic_value: Intrinsic value per share.
        upside: Upside percentage.
        recommendation: Recommendation string.
    """

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
    """
    Screen endpoint response payload.

    Attributes:
        results: List of screening results.
        total: Number of results returned.
    """

    model_config = ConfigDict(populate_by_name=True)

    results: list[ScreenItemData] = Field(default_factory=list, description="Screening results.")
    total: int = Field(..., ge=0, description="Number of results returned.")
