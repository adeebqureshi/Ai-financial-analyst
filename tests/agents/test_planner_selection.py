"""
Tests for the planner's tool-selection behaviour (Phase 4B test cases).

Each case verifies that the planner selects ONLY the tools necessary for the
question, never speculatively running every capability.
"""

from app.agents.planner import PlannerAgent


def _tools(query: str, **kwargs) -> list[str]:
    return PlannerAgent().plan(query, **kwargs).tool_names


def _unique_tools(query: str, **kwargs) -> set[str]:
    return set(_tools(query, **kwargs))


# ──────────────────────────────────────────────────────────────────────
# TEST 1 — pure market data
# ──────────────────────────────────────────────────────────────────────


def test_price_question_runs_market_data_only():
    assert _tools("What is Apple's current price?") == ["get_market_data"]


# ──────────────────────────────────────────────────────────────────────
# TEST 2 — valuation
# ──────────────────────────────────────────────────────────────────────


def test_undervalued_runs_financials_and_valuation():
    tools = set(_tools("Is Apple undervalued?"))

    assert {"get_financials", "calculate_valuation", "get_market_data"} <= tools

    assert "search_documents" not in tools

    assert "calculate_risk" not in tools


# ──────────────────────────────────────────────────────────────────────
# TEST 3 — RAG only
# ──────────────────────────────────────────────────────────────────────


def test_annual_report_question_runs_rag_only():
    assert _tools(
        "What does Apple's annual report say about supply chain risk?"
    ) == ["search_documents"]

    assert _tools(
        "What does Apple's 10-K say about supply chain risks?"
    ) == ["search_documents"]


# ──────────────────────────────────────────────────────────────────────
# TEST 4 — financial health
# ──────────────────────────────────────────────────────────────────────


def test_financial_health_runs_health_tools():
    tools = set(_tools("Is Apple financially healthy?"))

    assert {"get_financials", "calculate_ratios", "calculate_financial_health"} <= tools

    assert "calculate_valuation" not in tools

    assert "get_market_data" not in tools


# ──────────────────────────────────────────────────────────────────────
# TEST 5 — comparison
# ──────────────────────────────────────────────────────────────────────


def test_compare_runs_comparison_and_company_data():
    plan = PlannerAgent().plan("Compare Apple and Microsoft.")

    assert plan.tickers == ["AAPL", "MSFT"]

    assert "compare_companies" in plan.tool_names

    # one set of company/financial data per ticker
    assert plan.tool_names.count("get_company") == 2

    assert plan.tool_names.count("get_financials") == 2

    assert "search_documents" not in plan.tool_names


# ──────────────────────────────────────────────────────────────────────
# TEST 6 — comparison + RAG
# ──────────────────────────────────────────────────────────────────────


def test_compare_with_annual_reports_adds_rag():
    plan = PlannerAgent().plan(
        "Compare Apple and Microsoft using their annual reports "
        "and tell me which is a better investment."
    )

    tools = set(plan.tool_names)

    assert "compare_companies" in tools

    assert "search_documents" in tools

    assert plan.tool_names.count("search_documents") == 2  # one per ticker

    assert plan.needs_rag is True


# ──────────────────────────────────────────────────────────────────────
# TEST 7 — mixed multi-step analysis
# ──────────────────────────────────────────────────────────────────────


def test_analysis_valuation_health_risk_document():
    plan = PlannerAgent().plan(
        "Analyze Nvidia's valuation, financial health, and risks "
        "mentioned in its annual report."
    )

    assert plan.tickers == ["NVDA"]

    tools = set(plan.tool_names)

    assert {
        "get_financials",
        "calculate_valuation",
        "calculate_financial_health",
        "calculate_risk",
        "search_documents",
    } <= tools

    assert plan.needs_rag is True


# ──────────────────────────────────────────────────────────────────────
# TEST 8 — unsupported by available documents
# ──────────────────────────────────────────────────────────────────────


def test_unsupported_document_question_plans_rag_without_extras():
    plan = PlannerAgent().plan(
        "What does Tesla's annual report say about CEO compensation in 2015?"
    )

    assert plan.tool_names == ["search_documents"]

    assert plan.tickers == ["TSLA"]


# ──────────────────────────────────────────────────────────────────────
# Conversational context
# ──────────────────────────────────────────────────────────────────────


def test_follow_up_resolves_pronoun_to_previous_ticker():
    planner = PlannerAgent()

    session = "test-session-1"

    planner.plan("Analyze Apple.", session_id=session)

    plan = planner.plan("Now compare it with Microsoft.", session_id=session)

    assert plan.tickers == ["AAPL", "MSFT"]

    assert "compare_companies" in plan.tool_names


def test_follow_up_resolves_which_one():
    planner = PlannerAgent()

    session = "test-session-2"

    planner.plan("Analyze Apple.", session_id=session)

    plan = planner.plan("Which one has better valuation?", session_id=session)

    assert plan.tickers == ["AAPL"]


# ──────────────────────────────────────────────────────────────────────
# TEST 9 — complex mixed question (Phase 5)
# ──────────────────────────────────────────────────────────────────────


def test_compare_nvidia_amd_mixed_uses_tools_and_rag():
    plan = PlannerAgent().plan(
        "Compare Nvidia and AMD using their financials and annual reports, "
        "assess valuation, health and risks."
    )

    assert plan.tickers == ["NVDA", "AMD"]

    tools = set(plan.tool_names)

    assert {
        "get_financials",
        "calculate_valuation",
        "calculate_financial_health",
        "calculate_risk",
        "search_documents",
        "compare_companies",
    } <= tools

    assert plan.needs_rag is True

    # one retrieval per company — never a cross-company RAG mix
    assert plan.tool_names.count("search_documents") == 2

    assert plan.tool_names.count("calculate_valuation") == 2

    assert plan.tool_names.count("calculate_risk") == 2


# ──────────────────────────────────────────────────────────────────────
# Conversational context — implicit follow-up without a pronoun (Phase 5)
# ──────────────────────────────────────────────────────────────────────


def test_follow_up_inherits_ticker_without_pronoun():
    planner = PlannerAgent()

    session = "test-session-3"

    planner.plan("Analyze Apple.", session_id=session)

    plan = planner.plan("What is the revenue?", session_id=session)

    assert plan.tickers == ["AAPL"]

    assert "get_financials" in plan.tool_names


def test_follow_up_does_not_leak_ticker_on_topic_switch():
    planner = PlannerAgent()

    session = "test-session-4"

    planner.plan("Analyze Apple.", session_id=session)

    plan = planner.plan("What is the weather today?", session_id=session)

    assert plan.tickers == []


def test_follow_up_switching_company_ignores_previous():
    planner = PlannerAgent()

    session = "test-session-5"

    planner.plan("Analyze Apple.", session_id=session)

    plan = planner.plan("Compare Nvidia and AMD.", session_id=session)

    assert plan.tickers == ["NVDA", "AMD"]

    assert "AAPL" not in plan.tickers
