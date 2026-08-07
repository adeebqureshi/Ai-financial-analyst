from app.agents.planner import PlannerAgent


def test_general_plan():

    planner = PlannerAgent()

    tasks = planner.plan(
        "Tell me about Apple."
    )

    assert len(tasks) == 2

    assert tasks[0].name == "Retrieve Documents"

    assert tasks[1].name == "Generate Report"


def test_dcf_plan():

    planner = PlannerAgent()

    tasks = planner.plan(
        "Calculate DCF valuation."
    )

    assert len(tasks) == 3

    assert tasks[1].name == "Run Valuation"