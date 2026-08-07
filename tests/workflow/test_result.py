from app.workflow.result import WorkflowResult
from app.workflow.state import WorkflowState


def test_result():

    state = WorkflowState(
        query="Apple",
    )

    state.finish("planner")

    result = WorkflowResult(
        state=state,
        success=True,
    )

    assert result.success

    assert result.completed_steps == 1