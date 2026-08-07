from app.workflow.state import WorkflowState


def test_state():

    state = WorkflowState(
        query="Apple"
    )

    state.set(
        "company",
        "Apple",
    )

    assert state.get(
        "company"
    ) == "Apple"

    state.finish(
        "planner"
    )

    assert state.completed == [
        "planner",
    ]