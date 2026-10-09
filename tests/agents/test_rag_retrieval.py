"""Regression tests for Research RAG routing of tickerless questions.

Bug: "What drove revenue growth?" and "find the total year profit" classified
as FINANCIAL_ANALYSIS with no ticker, so the planner emitted zero tools and the
chat fell back to "insufficient evidence" without ever searching Qdrant.
"""
from app.agents.intents import AgentIntent
from app.agents.planner import PlannerAgent


def test_tickerless_financial_question_routes_to_document_search():
    planner = PlannerAgent()
    plan = planner.plan("What drove revenue growth?")
    assert plan.tool_names == ["search_documents"]
    assert plan.needs_rag is True


def test_tickerless_profit_question_routes_to_document_search():
    planner = PlannerAgent()
    plan = planner.plan("find the total year profit")
    assert plan.tool_names == ["search_documents"]
    assert plan.needs_rag is True


def test_document_id_scoped_tickerless_search():
    planner = PlannerAgent()
    plan = planner.plan("What drove revenue growth?", document_id="doc-1")
    assert plan.tool_names == ["search_documents"]
    assert plan.tools[0].args.get("document_id") == "doc-1"


def test_ticker_financial_question_does_not_search_documents():
    planner = PlannerAgent()
    plan = planner.plan("Analyze Apple's profitability.")
    assert "search_documents" not in plan.tool_names
    assert "get_financials" in plan.tool_names


def test_price_question_still_market_data_only():
    planner = PlannerAgent()
    plan = planner.plan("What is Apple's current price?")
    assert plan.tool_names == ["get_market_data"]
    assert plan.tickers == ["AAPL"]


def test_explicit_document_question_still_rag_only():
    planner = PlannerAgent()
    plan = planner.plan(
        "What does Apple's annual report say about supply chain risk?"
    )
    assert plan.tool_names == ["search_documents"]
    assert plan.needs_rag is True


def test_company_research_with_ticker_unchanged():
    planner = PlannerAgent()
    plan = planner.plan("Tell me about Apple.")
    assert "get_company" in plan.tool_names
    assert "get_financials" in plan.tool_names


def test_summarize_key_risks_routes_to_document_search():
    """Tickerless RISK_ANALYSIS used to plan zero tools -> insufficient evidence.

    "Summarize key risks" classifies as RISK_ANALYSIS only. The sole risk tool
    (calculate_risk) is ticker-scoped, so with no ticker the plan was empty and
    the analyst returned the fallback without ever querying Qdrant. Risk factors
    (Item 1A) live in the uploaded 10-K, so the planner must search documents.
    """
    planner = PlannerAgent()
    plan = planner.plan("Summarize key risks")
    assert plan.intents == [AgentIntent.RISK_ANALYSIS]
    assert plan.tickers == []
    assert plan.tool_names == ["search_documents"]
    assert plan.needs_rag is True
    assert "ticker" not in plan.tools[0].args


def test_major_risks_with_ticker_searches_documents():
    planner = PlannerAgent()
    plan = planner.plan("What are Apple's major risks?")
    assert plan.tickers == ["AAPL"]
    assert "search_documents" in plan.tool_names
    assert plan.needs_rag is True
    search = next(t for t in plan.tools if t.tool == "search_documents")
    assert search.args["ticker"] == "AAPL"
    # Quantitative risk tooling is still planned alongside the document search.
    assert "calculate_risk" in plan.tool_names


def test_tickerless_supply_chain_risk_question_searches_documents():
    planner = PlannerAgent()
    plan = planner.plan("What are the major supply-chain risks?")
    assert plan.tickers == []
    assert plan.tool_names == ["search_documents"]
    assert plan.needs_rag is True


def test_tickerless_risk_question_honours_document_id_scope():
    planner = PlannerAgent()
    plan = planner.plan("Summarize key risks", document_id="doc-1")
    assert plan.tool_names == ["search_documents"]
    assert plan.tools[0].args.get("document_id") == "doc-1"


def test_compare_margins_by_segment_path_unchanged():
    """Guards the working quick action against regression."""
    planner = PlannerAgent()
    plan = planner.plan("Compare margins by segment")
    assert plan.intents == [
        AgentIntent.COMPARISON,
        AgentIntent.FINANCIAL_ANALYSIS,
    ]
    assert plan.tickers == []
    assert plan.tool_names == ["search_documents"]
    assert plan.needs_rag is True
    assert plan.tools[0].args == {"query": "Compare margins by segment"}


def test_document_and_risk_intent_does_not_duplicate_search():
    plan = PlannerAgent().plan(
        "Summarize key risks mentioned in this 10-K?", document_id="doc-1"
    )
    assert plan.tool_names.count("search_documents") == 1
    assert plan.needs_rag is True


def test_price_question_not_pulled_into_document_search_by_fix():
    planner = PlannerAgent()
    plan = planner.plan("What is Apple's current price?")
    assert "search_documents" not in plan.tool_names
    assert plan.needs_rag is False


def test_non_risk_ticker_question_not_pulled_into_document_search():
    planner = PlannerAgent()
    plan = planner.plan("Analyze Apple's profitability.")
    assert "search_documents" not in plan.tool_names
    assert plan.needs_rag is False
