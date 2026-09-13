"""
planner.py

The planner decides *which existing capabilities* are required to answer a
question and returns a minimal, ordered set of tool calls. It never runs a
tool and never invokes an LLM — classification is deterministic.

Design Decisions:
    - **Intent → tools mapping**: Each intent maps to the smallest set of tools
      that can produce an evidence-backed answer. A pure price question runs
      exactly one tool (``get_market_data``); a document question runs only
      ``search_documents``.
    - **Ticker scoping**: Every company-specific tool carries the exact ticker
      it should operate on, and ``search_documents`` is scoped to the ticker
      so retrieval never leaks across companies.
    - **Conversational context**: When a ``session_id`` is supplied, pronouns
      are resolved against the previous turn before classification.
"""

from __future__ import annotations

from app.agents.companies import detect_tickers
from app.agents.intents import AgentIntent, IntentClassifier
from app.agents.memory import ConversationMemory
from app.agents.research_plan import ResearchPlan, ToolCall
from app.utils.tickers import normalize_ticker


class PlannerAgent:
    """
    Plans the sequence of tool calls needed to answer a user request.
    """

    def __init__(self) -> None:
        self.classifier = IntentClassifier()
        self.memory = ConversationMemory()

    def plan(
        self,
        query: str,
        ticker: str | None = None,
        document_id: str | None = None,
        session_id: str | None = None,
        owner_id: str | None = None,
    ) -> ResearchPlan:
        """
        Build the research plan for ``query``.

        Args:
            query: The user question.
            ticker: Explicit ticker supplied by the caller (e.g. from the chat
                request) — used when the query itself carries no ticker.
            document_id: Optional document the question is scoped to.
            session_id: Optional session used to resolve follow-up references.
            owner_id: Optional owner id scoping session context (tenant
                isolation — follow-up memory is keyed per owner).

        Returns:
            A :class:`ResearchPlan` with the minimal tool set.
        """
        resolved_query, resolved_tickers = self._resolve_context(
            query=query,
            ticker=ticker,
            session_id=session_id,
            owner_id=owner_id,
        )

        intents = self.classifier.classify(
            resolved_query,
            document_id=document_id,
        )

        tickers = self._apply_request_ticker(
            resolved_tickers,
            ticker,
            resolved_query,
            intents,
        )

        plan = ResearchPlan(
            query=resolved_query,
            intents=intents,
            tickers=tickers,
        )

        self._build_tools(
            plan,
            query=resolved_query,
            document_id=document_id,
        )

        plan.reasoning = self._reason(plan)

        # Make the planner self-sufficient for follow-ups even when it is used
        # standalone (outside the coordinator's run loop).
        if session_id and tickers:
            self.memory.remember(
                session_id,
                tickers,
                resolved_query,
                "",
                owner_id=owner_id,
            )

        return plan

    # ──────────────────────────────────────────────────────────────────
    # Context resolution
    # ──────────────────────────────────────────────────────────────────

    def _resolve_context(
        self,
        query: str,
        ticker: str | None,
        session_id: str | None,
        *,
        owner_id: str | None = None,
    ) -> tuple[str, list[str]]:
        detected = detect_tickers(query)

        tickers = self.memory.resolve_tickers(
            query,
            detected,
            session_id,
            owner_id=owner_id,
        )

        return query, tickers

    def _apply_request_ticker(
        self,
        detected: list[str],
        request_ticker: str | None,
        query: str,
        intents: list[AgentIntent],
    ) -> list[str]:
        """
        Ensure a ticker explicitly passed by the client is honoured.

        A client-supplied ticker is authoritative for company questions; it is
        not applied to pure document questions ("what does the 10-K say about
        supply chain?") where the question does not reference a company.
        """
        if not request_ticker:
            return detected

        try:
            normalized = normalize_ticker(request_ticker)
        except ValueError:
            # The explicit ticker is untrusted input. In the standard chat flow
            # it is already validated by the request schema; if a caller passes
            # an invalid value directly, discard it rather than propagate a
            # malicious symbol into the tool calls / provider requests.
            return detected

        if normalized in detected:
            return detected

        # Use classifier intents to determine if this is a company question
        intent_names = {intent.value for intent in intents}
        company_intents = {
            AgentIntent.VALUATION.value,
            AgentIntent.FINANCIAL_ANALYSIS.value,
            AgentIntent.RISK_ANALYSIS.value,
            AgentIntent.COMPARISON.value,
            AgentIntent.COMPANY_RESEARCH.value,
            AgentIntent.REPORT_GENERATION.value,
            AgentIntent.PORTFOLIO_ANALYSIS.value,
            AgentIntent.CALCULATION.value,
        }
        is_company_question = bool(intent_names & company_intents)

        if is_company_question or not detected:
            return [normalized]

        return detected

    # ──────────────────────────────────────────────────────────────────
    # Tool selection (the core of the planner)
    # ──────────────────────────────────────────────────────────────────

    def _build_tools(
        self,
        plan: ResearchPlan,
        query: str,
        document_id: str | None,
    ) -> None:
        intent_names = {intent.value for intent in plan.intents}

        # A pure financial-health question must only run the tools needed to
        # assess health (financials + ratios + health score). It must not
        # speculatively run valuation (DCF) or pull live market data, nor fetch
        # a company profile. This is disabled when the question also expresses a
        # valuation/risk/comparison/portfolio/report/document intent.
        text = f" {query.lower()} "

        health_only = (
            AgentIntent.FINANCIAL_ANALYSIS.value in intent_names
            and not any(
                name in intent_names
                for name in (
                    AgentIntent.VALUATION.value,
                    AgentIntent.RISK_ANALYSIS.value,
                    AgentIntent.COMPARISON.value,
                    AgentIntent.PORTFOLIO_ANALYSIS.value,
                    AgentIntent.REPORT_GENERATION.value,
                    AgentIntent.DOCUMENT_RESEARCH.value,
                )
            )
            and _is_health_only_question(text)
        )

        tools: list[ToolCall] = []
        seen: set[tuple[str, str]] = set()

        def add(tool: str, args: dict, label: str) -> None:
            key = (tool, str(args))
            if key in seen:
                return
            seen.add(key)
            tools.append(ToolCall(tool=tool, args=args, label=label))

        # ── Document retrieval ────────────────────────────────────────
        if AgentIntent.DOCUMENT_RESEARCH.value in intent_names:
            plan.needs_rag = True

            if plan.tickers:
                for ticker in plan.tickers:
                    args: dict[str, object] = {"query": query, "ticker": ticker}
                    if document_id:
                        args["document_id"] = document_id
                    add(
                        "search_documents",
                        args,
                        f"Searched {ticker} documents",
                    )
            else:
                args = {"query": query}
                if document_id:
                    args["document_id"] = document_id
                add(
                    "search_documents",
                    args,
                    "Searched uploaded documents",
                )

        # ── Pure price question: market data only ─────────────────────
        # Classifier returns only MARKET_DATA for pure price questions.
        if AgentIntent.MARKET_DATA.value in intent_names:
            for ticker in plan.tickers:
                add(
                    "get_market_data",
                    {"ticker": ticker},
                    f"Retrieved market data for {ticker}",
                )
            plan.tools = tools
            return

        # ── Company profile ───────────────────────────────────────────
        if not health_only and any(
            name in intent_names
            for name in (
                AgentIntent.FINANCIAL_ANALYSIS.value,
                AgentIntent.COMPANY_RESEARCH.value,
                AgentIntent.COMPARISON.value,
                AgentIntent.REPORT_GENERATION.value,
            )
        ):
            for ticker in plan.tickers:
                add(
                    "get_company",
                    {"ticker": ticker},
                    f"Retrieved company profile for {ticker}",
                )

        # ── Financial data (statements + risk scores) ─────────────────
        if any(
            name in intent_names
            for name in (
                AgentIntent.FINANCIAL_ANALYSIS.value,
                AgentIntent.VALUATION.value,
                AgentIntent.RISK_ANALYSIS.value,
                AgentIntent.COMPARISON.value,
                AgentIntent.REPORT_GENERATION.value,
                AgentIntent.PORTFOLIO_ANALYSIS.value,
                AgentIntent.COMPANY_RESEARCH.value,
                AgentIntent.CALCULATION.value,
            )
        ):
            for ticker in plan.tickers:
                add(
                    "get_financials",
                    {"ticker": ticker},
                    f"Retrieved financial statements for {ticker}",
                )

        # ── Market data (live snapshot for analysis/valuation) ────────
        if not health_only and any(
            name in intent_names
            for name in (
                AgentIntent.VALUATION.value,
                AgentIntent.FINANCIAL_ANALYSIS.value,
            )
        ):
            for ticker in plan.tickers:
                add(
                    "get_market_data",
                    {"ticker": ticker},
                    f"Retrieved market data for {ticker}",
                )

        # ── Ratios (financial health / analysis / comparison) ─────────
        if any(
            name in intent_names
            for name in (
                AgentIntent.FINANCIAL_ANALYSIS.value,
                AgentIntent.COMPARISON.value,
            )
        ):
            for ticker in plan.tickers:
                add(
                    "calculate_ratios",
                    {"ticker": ticker},
                    f"Computed ratios for {ticker}",
                )

        # ── Valuation (DCF) ───────────────────────────────────────────
        if (
            not health_only
            and (
                AgentIntent.FINANCIAL_ANALYSIS.value in intent_names
                or AgentIntent.VALUATION.value in intent_names
                or AgentIntent.COMPARISON.value in intent_names
                or AgentIntent.REPORT_GENERATION.value in intent_names
            )
        ):
            for ticker in plan.tickers:
                add(
                    "calculate_valuation",
                    {"ticker": ticker},
                    f"Ran DCF valuation for {ticker}",
                )

        # ── Financial health ──────────────────────────────────────────
        if any(
            name in intent_names
            for name in (
                AgentIntent.FINANCIAL_ANALYSIS.value,
                AgentIntent.COMPARISON.value,
                AgentIntent.REPORT_GENERATION.value,
            )
        ):
            for ticker in plan.tickers:
                add(
                    "calculate_financial_health",
                    {"ticker": ticker},
                    f"Assessed financial health for {ticker}",
                )

        # ── Risk ──────────────────────────────────────────────────────
        if any(
            name in intent_names
            for name in (
                AgentIntent.RISK_ANALYSIS.value,
                AgentIntent.COMPARISON.value,
            )
        ):
            for ticker in plan.tickers:
                add(
                    "calculate_risk",
                    {"ticker": ticker},
                    f"Assessed financial risk for {ticker}",
                )

        # ── Custom sandboxed calculations ─────────────────────────────
        # Deterministic engines (valuation/DCF) still handle their own
        # questions; the sandbox is only used when the user explicitly asks
        # for a calculation that the fixed engine set does not cover.
        if (
            AgentIntent.CALCULATION.value in intent_names
            and AgentIntent.VALUATION.value not in intent_names
        ):
            if plan.tickers:
                for ticker in plan.tickers:
                    add(
                        "run_calculation",
                        {"question": query, "ticker": ticker},
                        f"Sandboxed calculation for {ticker}",
                    )
            else:
                add(
                    "run_calculation",
                    {"question": query},
                    "Sandboxed calculation",
                )

        # ── Comparison ────────────────────────────────────────────────
        if AgentIntent.COMPARISON.value in intent_names and len(plan.tickers) >= 2:
            add(
                "compare_companies",
                {"tickers": plan.tickers},
                "Compared " + " vs ".join(plan.tickers),
            )

        # ── Report generation ─────────────────────────────────────────
        if AgentIntent.REPORT_GENERATION.value in intent_names and plan.tickers:
            add(
                "generate_report",
                {"ticker": plan.tickers[0], "query": query},
                f"Generated investment report for {plan.tickers[0]}",
            )

        plan.tools = tools

    # ──────────────────────────────────────────────────────────────────
    # Reasoning summary (safe, high-level steps only)
    # ──────────────────────────────────────────────────────────────────

    @staticmethod
    def _reason(plan: ResearchPlan) -> list[str]:
        intent_labels = {
            AgentIntent.MARKET_DATA.value: "Market data question",
            AgentIntent.DOCUMENT_RESEARCH.value: "Document research question",
            AgentIntent.COMPANY_RESEARCH.value: "Company research question",
            AgentIntent.FINANCIAL_ANALYSIS.value: "Financial analysis question",
            AgentIntent.VALUATION.value: "Valuation question",
            AgentIntent.RISK_ANALYSIS.value: "Risk analysis question",
            AgentIntent.COMPARISON.value: "Company comparison question",
            AgentIntent.PORTFOLIO_ANALYSIS.value: "Portfolio question",
            AgentIntent.REPORT_GENERATION.value: "Report generation question",
            AgentIntent.CALCULATION.value: "Calculation question",
        }

        reasons = [
            intent_labels[intent.value]
            for intent in plan.intents
            if intent.value in intent_labels
        ]

        if plan.tools:
            reasons.append(
                "Selected tools: " + ", ".join(plan.tool_names)
            )

        return reasons

_HEALTH_PHRASE_KEYWORDS = (
    "financially healthy",
    "financial health",
    "healthy",
    "solvency",
    "liquidity",
    "strong balance sheet",
    "financial strength",
)

_ANALYSIS_ACTION_KEYWORDS = (
    "analyze",
    "analysis",
    "fundamentals",
    "profitability",
)


def _is_health_only_question(text: str) -> bool:
    """
    True when the question is specifically about financial health and is not a
    general company analysis request (which would also need company/market data
    and a valuation).
    """
    if not any(keyword in text for keyword in _HEALTH_PHRASE_KEYWORDS):
        return False

    if any(keyword in text for keyword in _ANALYSIS_ACTION_KEYWORDS):
        return False

    return True


