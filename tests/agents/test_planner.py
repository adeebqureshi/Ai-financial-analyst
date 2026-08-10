from app.agents.planner import PlannerAgent


def test_market_data_plan():
    planner = PlannerAgent()

    plan = planner.plan(
        "What is Apple's current price?"
    )

    assert plan.tool_names == ["get_market_data"]

    assert plan.tickers == ["AAPL"]


def test_valuation_plan():
    planner = PlannerAgent()

    plan = planner.plan(
        "Is Apple undervalued?"
    )

    assert "get_financials" in plan.tool_names

    assert "calculate_valuation" in plan.tool_names

    assert plan.tickers == ["AAPL"]


def test_document_plan_uses_rag_only():
    planner = PlannerAgent()

    plan = planner.plan(
        "What does Apple's annual report say about supply chain risk?"
    )

    assert plan.tool_names == ["search_documents"]

    assert plan.needs_rag is True


def test_company_research_fallback():
    planner = PlannerAgent()

    plan = planner.plan(
        "Tell me about Apple."
    )

    assert "get_company" in plan.tool_names

    assert "get_financials" in plan.tool_names

    assert plan.tickers == ["AAPL"]
