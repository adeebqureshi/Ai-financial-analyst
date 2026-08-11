"""
tools.py

Clean tool layer for the agentic research pipeline.

Every tool wraps an *existing* service / engine — the same services the REST
endpoints use. The agent (planner + coordinator) decides which tools to run;
each tool performs the actual operation and returns structured data. No
financial calculation lives inside an LLM prompt, and no new service or
engine is introduced here.

Design Decisions:
    - **Single registry**: ``ToolRegistry.execute()`` dispatches a ``ToolCall``
      to the matching handler and always returns a structured ``ToolResult``
      (never raises into the orchestrator).
    - **Error isolation**: A failed tool produces a ``status="error"`` result;
      the coordinator continues with the remaining evidence and reports the
      gap instead of fabricating a value.
    - **Ticker isolation**: Every company tool uppercases the requested ticker
      and uses it to fetch that company's own data. ``search_documents``
      filters retrieved chunks by the requested ticker so an Apple question
      never surfaces Microsoft documents.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from app.agents.companies import TICKER_HINTS, company_names_for
from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.financial.altman import AltmanZScore
from app.financial.beneish import BeneishMScore
from app.financial.data import CompanyFinancialData, FinancialDataService
from app.financial.health import FinancialHealth
from app.financial.ratios import FinancialRatios
from app.financial.valuation import ValuationEngine
from app.financial.wacc import WACC
from app.ingestion.services.market_service import MarketService
from app.services.company_service import CompanyService
from app.services.compare_service import CompareService
from app.services.document_service import DocumentService
from app.services.report_service import ReportService

logger = get_logger(__name__)

_RISK_FREE_RATE = 0.0425
_MARKET_RETURN = 0.10
_COST_OF_DEBT = 0.05

DEFAULT_RETRIEVAL_LIMIT = 5


@dataclass(slots=True)
class ToolResult:
    """
    Structured result of one tool execution.

    Attributes:
        tool: The tool name.
        status: ``done`` or ``error``.
        detail: Short human-readable summary (for the tool-transparency UI).
        result: Structured tool output (dict) or ``None`` on error.
        error: Error message when ``status == "error"``.
    """

    tool: str
    status: str
    detail: str
    result: dict[str, Any] | None = None
    error: str | None = None


# Tool metadata used for introspection and the UI (name -> description).
TOOL_DESCRIPTIONS: dict[str, str] = {
    "get_company": "Retrieve the company profile (name, sector, industry, description).",
    "get_market_data": "Retrieve live market data (price, market cap, volume, beta).",
    "get_financials": "Retrieve the company's real financial statements and risk scores.",
    "calculate_ratios": "Compute financial ratios from the company's real statements.",
    "calculate_valuation": "Run a DCF valuation using the company's real financials.",
    "calculate_financial_health": "Compute the composite financial health score.",
    "calculate_risk": "Assess financial risk (health, Altman, Beneish).",
    "compare_companies": "Compare multiple companies using each company's own data.",
    "search_documents": "Search uploaded documents with source metadata.",
    "generate_report": "Generate a structured markdown investment report.",
}

Handler = Callable[[dict[str, Any]], ToolResult]


def _statement_payload(data: CompanyFinancialData) -> dict[str, float]:
    statement = data.statement
    return {
        "revenue": statement.revenue,
        "operating_income": statement.operating_income,
        "net_income": statement.net_income,
        "total_assets": statement.total_assets,
        "total_liabilities": statement.total_liabilities,
        "cash": statement.cash,
        "debt": statement.debt,
        "shares_outstanding": statement.shares_outstanding,
        "free_cash_flow": statement.free_cash_flow,
    }


def _exchange_value(exchange) -> str | None:
    if exchange is None:
        return None
    return getattr(exchange, "value", str(exchange))


class ToolRegistry:
    """
    Registry + executor for the agent's available tools.
    """

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        financials: FinancialDataService | None = None,
        market: MarketService | None = None,
        company: CompanyService | None = None,
        compare: CompareService | None = None,
        documents: DocumentService | None = None,
        report: ReportService | None = None,
    ) -> None:
        settings = settings or get_settings()

        self._financials = financials or FinancialDataService()
        self._market = market or MarketService()
        self._company = company or CompanyService(settings)
        self._compare = compare or CompareService(settings)
        self._documents = documents or DocumentService(settings)
        self._report = report or ReportService(settings)

        self._valuation = ValuationEngine()

        self._handlers: dict[str, Handler] = {
            "get_company": self._get_company,
            "get_market_data": self._get_market_data,
            "get_financials": self._get_financials,
            "calculate_ratios": self._calculate_ratios,
            "calculate_valuation": self._calculate_valuation,
            "calculate_financial_health": self._calculate_financial_health,
            "calculate_risk": self._calculate_risk,
            "compare_companies": self._compare_companies,
            "search_documents": self._search_documents,
            "generate_report": self._generate_report,
        }

    @property
    def available_tools(self) -> list[str]:
        """Names of every tool this agent can run."""
        return list(self._handlers)

    # ──────────────────────────────────────────────────────────────────
    # Dispatch
    # ──────────────────────────────────────────────────────────────────

    def execute(
        self,
        tool: str,
        args: dict[str, Any],
    ) -> ToolResult:
        """
        Execute a single tool call, always returning a ``ToolResult``.
        """
        handler = self._handlers.get(tool)

        if handler is None:
            return ToolResult(
                tool=tool,
                status="error",
                detail=f"Unknown tool '{tool}'.",
                error="unknown_tool",
            )

        try:
            return handler(args)
        except Exception as exc:
            logger.warning("Tool '%s' failed: %s", tool, exc)
            return ToolResult(
                tool=tool,
                status="error",
                detail=f"Failed to {tool.replace('_', ' ')}.",
                error=str(exc),
            )

    # ──────────────────────────────────────────────────────────────────
    # Company data
    # ──────────────────────────────────────────────────────────────────

    def _get_company(self, args: dict[str, Any]) -> ToolResult:
        ticker = str(args["ticker"]).upper()

        data = self._company.get_company(ticker)

        return ToolResult(
            tool="get_company",
            status="done",
            detail=f"Retrieved company profile for {ticker}",
            result={
                "ticker": data.ticker,
                "name": data.name,
                "sector": data.sector,
                "industry": data.industry,
                "market_cap": data.market_cap,
                "description": data.description,
            },
        )

    # ──────────────────────────────────────────────────────────────────
    # Market data
    # ──────────────────────────────────────────────────────────────────

    def _get_market_data(self, args: dict[str, Any]) -> ToolResult:
        ticker = str(args["ticker"]).upper()

        market = self._market.get_market_data(ticker)

        return ToolResult(
            tool="get_market_data",
            status="done",
            detail=f"Retrieved live market data for {ticker}",
            result={
                "ticker": market.ticker.upper(),
                "exchange": _exchange_value(market.exchange),
                "current_price": market.current_price,
                "currency": market.currency,
                "market_cap": market.market_cap,
                "volume": market.volume,
                "beta": market.beta,
                "pe_ratio": market.pe_ratio,
                "eps": market.eps,
                "dividend_yield": market.dividend_yield,
                "week_52_high": market.week_52_high,
                "week_52_low": market.week_52_low,
            },
        )

    # ──────────────────────────────────────────────────────────────────
    # Financial statements
    # ──────────────────────────────────────────────────────────────────

    def _get_financials(self, args: dict[str, Any]) -> ToolResult:
        ticker = str(args["ticker"]).upper()

        data = self._financials.load(ticker)

        return ToolResult(
            tool="get_financials",
            status="done",
            detail=f"Retrieved financial statements for {ticker}",
            result={
                "ticker": data.ticker,
                "name": data.name,
                "sector": data.sector,
                "industry": data.industry,
                "market_cap": data.market_cap,
                "description": data.description,
                "current_price": data.current_price,
                "growth_rate": data.growth_rate,
                "beta": data.beta,
                "tax_rate": data.tax_rate,
                "piotroski_score": data.piotroski_score,
                "altman_score": data.altman_score,
                "beneish_score": data.beneish_score,
                "statement": _statement_payload(data),
            },
        )

    # ──────────────────────────────────────────────────────────────────
    # Ratios
    # ──────────────────────────────────────────────────────────────────

    def _calculate_ratios(self, args: dict[str, Any]) -> ToolResult:
        ticker = str(args["ticker"]).upper()

        data = self._financials.load(ticker)

        statement = data.statement

        return ToolResult(
            tool="calculate_ratios",
            status="done",
            detail=f"Computed financial ratios for {ticker}",
            result={
                "ticker": ticker,
                "debt_to_equity": FinancialRatios.debt_to_equity(statement),
                "return_on_assets": FinancialRatios.return_on_assets(statement),
                "return_on_equity": FinancialRatios.return_on_equity(statement),
                "operating_margin": FinancialRatios.operating_margin(statement),
                "net_margin": FinancialRatios.net_margin(statement),
            },
        )

    # ──────────────────────────────────────────────────────────────────
    # Valuation (DCF)
    # ──────────────────────────────────────────────────────────────────

    def _calculate_valuation(self, args: dict[str, Any]) -> ToolResult:
        ticker = str(args["ticker"]).upper()

        data = self._financials.load(ticker)

        result = self._valuation.evaluate(
            statement=data.statement,
            current_price=data.current_price or 1.0,
            growth_rate=data.growth_rate,
            risk_free_rate=_RISK_FREE_RATE,
            beta=data.beta or 1.0,
            market_return=_MARKET_RETURN,
            tax_rate=data.tax_rate,
        )

        equity = data.statement.total_assets - data.statement.total_liabilities
        cost_of_equity = WACC.cost_of_equity(
            risk_free_rate=_RISK_FREE_RATE,
            beta=data.beta or 1.0,
            market_return=_MARKET_RETURN,
        )
        try:
            discount_rate = WACC.calculate(
                equity=equity,
                debt=data.statement.debt,
                cost_of_equity=cost_of_equity,
                cost_of_debt=_COST_OF_DEBT,
                tax_rate=data.tax_rate,
            )
        except ValueError:
            discount_rate = 0.0

        return ToolResult(
            tool="calculate_valuation",
            status="done",
            detail=f"Ran DCF valuation for {ticker}",
            result={
                "ticker": ticker,
                "current_price": data.current_price or 0.0,
                "intrinsic_value": result.intrinsic_value,
                "upside": result.upside,
                "recommendation": result.recommendation,
                "discount_rate": discount_rate,
            },
        )

    # ──────────────────────────────────────────────────────────────────
    # Financial health
    # ──────────────────────────────────────────────────────────────────

    def _calculate_financial_health(self, args: dict[str, Any]) -> ToolResult:
        ticker = str(args["ticker"]).upper()

        data = self._financials.load(ticker)

        score = FinancialHealth.score(
            data.piotroski_score,
            data.altman_score,
            data.beneish_score,
        )

        return ToolResult(
            tool="calculate_financial_health",
            status="done",
            detail=f"Assessed financial health for {ticker}",
            result={
                "ticker": ticker,
                "score": score,
                "rating": FinancialHealth.rating(score),
                "piotroski_score": data.piotroski_score,
                "altman_score": data.altman_score,
                "beneish_score": data.beneish_score,
            },
        )

    # ──────────────────────────────────────────────────────────────────
    # Risk analysis
    # ──────────────────────────────────────────────────────────────────

    def _calculate_risk(self, args: dict[str, Any]) -> ToolResult:
        ticker = str(args["ticker"]).upper()

        data = self._financials.load(ticker)

        health_score = FinancialHealth.score(
            data.piotroski_score,
            data.altman_score,
            data.beneish_score,
        )
        health_rating = FinancialHealth.rating(health_score)

        altman_int = AltmanZScore.interpretation(data.altman_score)
        beneish_int = BeneishMScore.interpretation(data.beneish_score)

        if health_score >= 85 and altman_int == "SAFE" and beneish_int == "LOW_RISK":
            risk_level = "LOW"
        elif health_score >= 50:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"

        return ToolResult(
            tool="calculate_risk",
            status="done",
            detail=f"Assessed financial risk for {ticker}",
            result={
                "ticker": ticker,
                "health_score": health_score,
                "health_rating": health_rating,
                "piotroski": {"score": data.piotroski_score, "max": 9},
                "altman": {"score": data.altman_score, "interpretation": altman_int},
                "beneish": {"score": data.beneish_score, "interpretation": beneish_int},
                "risk_level": risk_level,
            },
        )

    # ──────────────────────────────────────────────────────────────────
    # Company comparison
    # ──────────────────────────────────────────────────────────────────

    def _compare_companies(self, args: dict[str, Any]) -> ToolResult:
        tickers = [str(t).upper() for t in args["tickers"]]

        result = self._compare.compare_tickers(tickers)

        return ToolResult(
            tool="compare_companies",
            status="done",
            detail="Compared " + " vs ".join(tickers),
            result={
                "results": [
                    {
                        "ticker": item.ticker,
                        "name": item.name,
                        "intrinsic_value": item.intrinsic_value,
                        "upside": item.upside,
                        "recommendation": item.recommendation,
                        "health_score": item.health_score,
                    }
                    for item in result.results
                ],
                "best": result.best,
            },
        )

    # ──────────────────────────────────────────────────────────────────
    # Document retrieval (RAG)
    # ──────────────────────────────────────────────────────────────────

    def _search_documents(self, args: dict[str, Any]) -> ToolResult:
        query = str(args["query"])
        ticker = str(args["ticker"]).upper() if args.get("ticker") else None
        document_id = args.get("document_id")
        limit = int(args.get("limit") or DEFAULT_RETRIEVAL_LIMIT)

        # When the retrieval is scoped to a company we pull a wider candidate
        # pool and then filter by ticker. This keeps the correct company's
        # chunks from being crowded out by other filings in the top-N, which
        # is what grounds an Apple question in Apple's own documents.
        candidate_limit = (
            max(limit * 3, DEFAULT_RETRIEVAL_LIMIT)
            if ticker
            else limit
        )

        context = self._documents.retrieve(
            query=query,
            limit=candidate_limit,
            document_id=document_id,
        )

        chunks = [
            {
                "document_id": chunk.document_id,
                "filename": chunk.filename,
                "page": chunk.page,
                "text": chunk.text,
                "score": chunk.score,
                "chunk_id": chunk.chunk_id,
                "section": chunk.section,
                "ticker": chunk.ticker,
            }
            for chunk in context.chunks
        ]

        ticker_filtered = False

        if ticker:
            filtered = [
                chunk
                for chunk in chunks
                if _chunk_belongs_to_ticker(chunk, ticker)
            ]
            if filtered:
                chunks = filtered[:limit]
                ticker_filtered = True

        return ToolResult(
            tool="search_documents",
            status="done",
            detail=(
                f"Searched annual reports for {ticker}"
                if ticker
                else "Searched uploaded documents"
            ),
            result={
                "query": query,
                "ticker": ticker,
                "ticker_filtered": ticker_filtered,
                "chunks": chunks,
                "total": len(chunks),
            },
        )

    # ──────────────────────────────────────────────────────────────────
    # Report generation
    # ──────────────────────────────────────────────────────────────────

    def _generate_report(self, args: dict[str, Any]) -> ToolResult:
        ticker = str(args["ticker"]).upper()
        query = str(args.get("query") or "")

        report = self._report.generate_ticker_report(ticker, query)

        return ToolResult(
            tool="generate_report",
            status="done",
            detail=f"Generated investment report for {ticker}",
            result={
                "ticker": report.ticker,
                "title": report.title,
                "content": report.content,
                "format": report.format,
            },
        )


def _chunk_belongs_to_ticker(chunk: dict[str, Any], ticker: str) -> bool:
    """
    True when a retrieved chunk belongs to ``ticker``.

    Chunks carry a best-effort ticker detected from their filename (see
    ``DocumentService._detect_ticker``), which may be a company name such as
    "Apple" rather than the symbol "AAPL". We therefore match on the metadata
    ticker, the company name → ticker hints, or a case-insensitive filename
    mention.
    """
    chunk_ticker = (chunk.get("ticker") or "").strip()

    if chunk_ticker and chunk_ticker.upper() == ticker:
        return True

    if chunk_ticker:
        for name, symbol in TICKER_HINTS:
            if chunk_ticker.lower() == name and symbol == ticker:
                return True

    filename = (chunk.get("filename") or "").lower()

    if ticker.lower() in filename:
        return True

    return any(name in filename for name in company_names_for(ticker))
