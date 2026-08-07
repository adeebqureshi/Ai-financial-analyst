from app.agents.planner import PlannerAgent


def test_valuation_plan():

    planner = PlannerAgent()

    tasks = planner.plan(
        "Perform DCF valuation of Apple"
    )

    assert tasks[0].name == "valuation"


def test_health_plan():

    planner = PlannerAgent()

    tasks = planner.plan(
        "Evaluate bankruptcy risk"
    )

    assert tasks[0].name == "health"


def test_analysis_plan():

    planner = PlannerAgent()

    tasks = planner.plan(
        "Analyze revenue growth"
    )

    assert tasks[0].name == "analysis"


def test_default_plan():

    planner = PlannerAgent()

    tasks = planner.plan(
        "Tell me about Apple"
    )

    assert tasks[0].name == "general"