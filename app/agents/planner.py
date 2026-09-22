from __future__ import annotations
from app.agents.companies import detect_tickers
from app.agents.intents import AgentIntent, IntentClassifier
from app.agents.memory import ConversationMemory
from app.agents.research_plan import ResearchPlan, ToolCall
from app.utils.tickers import normalize_ticker
class PlannerAgent:
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
        if session_id and tickers:
            self.memory.remember(
                session_id,
                tickers,
                resolved_query,
                "",
                owner_id=owner_id,
            )
        return plan
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
        if not request_ticker:
            return detected
        try:
            normalized = normalize_ticker(request_ticker)
        except ValueError:
            return detected
        if normalized in detected:
            return detected
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
    def _build_tools(
        self,
        plan: ResearchPlan,
        query: str,
        document_id: str | None,
    ) -> None:
        intent_names = {intent.value for intent in plan.intents}
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
        if AgentIntent.MARKET_DATA.value in intent_names:
            for ticker in plan.tickers:
                add(
                    "get_market_data",
                    {"ticker": ticker},
                    f"Retrieved market data for {ticker}",
                )
            plan.tools = tools
            return
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
        if AgentIntent.COMPARISON.value in intent_names and len(plan.tickers) >= 2:
            add(
                "compare_companies",
                {"tickers": plan.tickers},
                "Compared " + " vs ".join(plan.tickers),
            )
        if AgentIntent.REPORT_GENERATION.value in intent_names and plan.tickers:
            add(
                "generate_report",
                {"ticker": plan.tickers[0], "query": query},
                f"Generated investment report for {plan.tickers[0]}",
            )
        plan.tools = tools
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
    if not any(keyword in text for keyword in _HEALTH_PHRASE_KEYWORDS):
        return False
    if any(keyword in text for keyword in _ANALYSIS_ACTION_KEYWORDS):
        return False
    return True