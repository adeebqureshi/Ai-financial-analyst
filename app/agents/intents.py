"""
intents.py

Intent classification for the agentic financial research pipeline.

The planner uses this classifier to decide *which* existing capabilities are
needed for a question. Classification is deterministic (keyword / phrase based)
so that tool selection is cheap, reproducible and testable — it never depends
on an LLM, and it never invokes any financial engine.

Design Decisions:
    - **Precedence over keywords**: ``DOCUMENT_RESEARCH`` questions ("what does
      the 10-K say about ...") are detected first so a bare document question
      does not accidentally trigger a DCF or a risk engine.
    - **Price shortcut**: A pure "what is the current price" question maps to a
      single ``MARKET_DATA`` intent so the planner selects only the market tool.
    - **Explicit intents only**: ``COMPARISON``, ``VALUATION``,
      ``FINANCIAL_ANALYSIS``, ``RISK_ANALYSIS``, ``REPORT_GENERATION`` and
      ``PORTFOLIO_ANALYSIS`` are reported when their phrases are present.
"""

from __future__ import annotations

from enum import Enum


class AgentIntent(str, Enum):
    """High-level question intents recognized by the planner."""

    MARKET_DATA = "MARKET_DATA"
    DOCUMENT_RESEARCH = "DOCUMENT_RESEARCH"
    COMPANY_RESEARCH = "COMPANY_RESEARCH"
    FINANCIAL_ANALYSIS = "FINANCIAL_ANALYSIS"
    VALUATION = "VALUATION"
    RISK_ANALYSIS = "RISK_ANALYSIS"
    COMPARISON = "COMPARISON"
    PORTFOLIO_ANALYSIS = "PORTFOLIO_ANALYSIS"
    REPORT_GENERATION = "REPORT_GENERATION"


_DOCUMENT_PHRASES = (
    "annual report",
    "10-k",
    "10k",
    "10-q",
    "10q",
    "20-f",
    "8-k",
    "filing",
    "according to",
    "what does",
    "does the report",
    "report say",
    "report says",
    "report state",
    "document",
    "documents",
    "mention",
    "mentions",
    "mentioned",
    "pdf",
    "uploaded",
    "in the report",
    "in its 10-k",
    "in their 10-k",
    "in its 10k",
    "in their 10k",
    "knowledge base",
)

_PRICE_PHRASES = (
    "current price",
    "stock price",
    "share price",
    "price of",
    "how much is",
    "what is the price",
    "what's the price",
    "quote",
    "price today",
    "market cap",
    "market capitalisation",
    "market capitalization",
)

_VALUATION_PHRASES = (
    "undervalued",
    "overvalued",
    "valuation",
    "dcf",
    "intrinsic value",
    "fair value",
    "price target",
    "trading below",
    "trading above",
    "cheap",
    "expensive",
    "worth",
    "upside",
)

_HEALTH_PHRASES = (
    "financially healthy",
    "financial health",
    "healthy",
    "solvency",
    "liquidity",
    "strong balance sheet",
    "financial strength",
)

_RISK_PHRASES = (
    "risk",
    "risky",
    "risks",
    "danger",
    "threat",
    "bankruptcy",
    "distress",
    "credit risk",
    "concentration risk",
)

_COMPARISON_PHRASES = (
    "compare",
    "comparison",
    "comparing",
    "versus",
    " vs ",
    "vs.",
    "which is better",
    "which is a better investment",
    "outperform",
    "better investment",
)

_REPORT_PHRASES = (
    "generate a report",
    "generate report",
    "write a report",
    "create a report",
    "investment thesis",
    "build an investment thesis",
    "research report",
    "investment research report",
)

_PORTFOLIO_PHRASES = (
    "portfolio",
    "my holdings",
    "diversification",
)

_ANALYSIS_PHRASES = (
    "analyze",
    "analysis",
    "financials",
    "financial statement",
    "financial statements",
    "balance sheet",
    "income statement",
    "cash flow",
    "cash flow statement",
    "fundamentals",
    "margins",
    "profitability",
    "growth",
    "revenue",
    "earnings",
    "how is",
    "how are",
)

# Phrase gate used to decide whether a *document* question also needs
# financial analysis tools. Topic words such as "risk", "revenue" or
# "report" (inside "annual report") must NOT flip a document question into a
# mixed question — only an explicit analytical request may do that.
_DOCUMENT_GATE_PHRASES = (
    "compare",
    "comparison",
    "versus",
    " vs ",
    "analyze",
    "analysis",
    "valuation",
    "undervalued",
    "overvalued",
    "dcf",
    "intrinsic value",
    "fair value",
    "price target",
    "financially healthy",
    "financial health",
    "generate a report",
    "generate report",
    "write a report",
    "create a report",
    "investment thesis",
    "investment research report",
    "portfolio",
)


def _contains(text: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in text for phrase in phrases)


class IntentClassifier:
    """
    Deterministic intent classifier for a user research question.
    """

    def classify(
        self,
        query: str,
        document_id: str | None = None,
    ) -> list[AgentIntent]:
        """
        Classify a question into one or more agent intents.

        Args:
            query: The user question.
            document_id: Optional document the question is explicitly scoped to.

        Returns:
            An ordered list of :class:`AgentIntent` values. The first entry is
            the dominant intent.
        """
        text = f" {query.lower()} "

        intents: list[AgentIntent] = []

        is_price = _contains(text, _PRICE_PHRASES)

        is_document = (
            bool(document_id)
            or _contains(text, _DOCUMENT_PHRASES)
        )

        has_financial_intent = any(
            _contains(text, phrases)
            for phrases in (
                _VALUATION_PHRASES,
                _HEALTH_PHRASES,
                _RISK_PHRASES,
                _COMPARISON_PHRASES,
                _ANALYSIS_PHRASES,
                _REPORT_PHRASES,
                _PORTFOLIO_PHRASES,
            )
        )

        # Pure market/price shortcut.
        if is_price and not has_financial_intent and not is_document:
            return [AgentIntent.MARKET_DATA]

        # Document-only questions must stay document-only (no DCF etc),
        # unless the question explicitly asks for an analytical capability.
        if is_document and not _contains(text, _DOCUMENT_GATE_PHRASES):
            return [AgentIntent.DOCUMENT_RESEARCH]

        if _contains(text, _COMPARISON_PHRASES):
            intents.append(AgentIntent.COMPARISON)

        if is_document:
            intents.append(AgentIntent.DOCUMENT_RESEARCH)

        if _contains(text, _VALUATION_PHRASES):
            intents.append(AgentIntent.VALUATION)

        if _contains(text, _HEALTH_PHRASES):
            intents.append(AgentIntent.FINANCIAL_ANALYSIS)

        if _contains(text, _RISK_PHRASES):
            intents.append(AgentIntent.RISK_ANALYSIS)

        if _contains(text, _PORTFOLIO_PHRASES):
            intents.append(AgentIntent.PORTFOLIO_ANALYSIS)

        if _contains(text, _REPORT_PHRASES):
            intents.append(AgentIntent.REPORT_GENERATION)

        if (
            _contains(text, _ANALYSIS_PHRASES)
            and AgentIntent.FINANCIAL_ANALYSIS not in intents
        ):
            intents.append(AgentIntent.FINANCIAL_ANALYSIS)

        # Company research fallback: a question that names a company but does
        # not map to any specific analysis capability.
        if not intents:
            intents.append(AgentIntent.COMPANY_RESEARCH)

        return intents
