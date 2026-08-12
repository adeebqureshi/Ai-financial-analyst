"""
Planner tests for calculation (sandbox) routing.

The sandbox is only used where LLM-generated calculations are required; the
deterministic engines must keep handling their own questions.
"""

from app.agents.planner import PlannerAgent


def test_wacc_question_plans_sandboxed_calculation():
    plan = PlannerAgent().plan("Calculate Apple's WACC")

    assert "run_calculation" in plan.tool_names
    assert "get_financials" in plan.tool_names
    assert plan.tickers == ["AAPL"]

    calc = next(call for call in plan.tools if call.tool == "run_calculation")
    assert calc.args["question"] == "Calculate Apple's WACC"
    assert calc.args["ticker"] == "AAPL"


def test_pure_math_question_plans_only_sandbox():
    plan = PlannerAgent().plan("compute 15 * 47")

    assert plan.tool_names == ["run_calculation"]
    assert plan.tickers == []


def test_npv_question_plans_sandbox_and_financials():
    plan = PlannerAgent().plan("what is the net present value for AAPL?")

    assert "run_calculation" in plan.tool_names
    assert "get_financials" in plan.tool_names


def test_valuation_question_keeps_deterministic_engine():
    """DCF/valuation stays on the deterministic engine — no sandbox."""
    plan = PlannerAgent().plan("Is Apple undervalued?")

    assert "run_calculation" not in plan.tool_names
    assert "calculate_valuation" in plan.tool_names


def test_price_question_keeps_market_tool():
    plan = PlannerAgent().plan("What is Apple's current price?")

    assert plan.tool_names == ["get_market_data"]
    assert "run_calculation" not in plan.tool_names


def test_document_question_stays_document_only():
    plan = PlannerAgent().plan(
        "What does Apple's annual report say about calculate supply chain risk?"
    )

    assert plan.tool_names == ["search_documents"]
    assert "run_calculation" not in plan.tool_names


def test_wacc_not_treated_as_ticker():
    """'WACC' is a financial acronym, not a company ticker."""
    plan = PlannerAgent().plan("calculate the wacc")

    assert plan.tickers == []
    assert "wacc" not in [t.lower() for t in plan.tickers]
