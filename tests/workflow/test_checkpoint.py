from app.workflow.checkpoint import WorkflowCheckpoint
from app.workflow.state import WorkflowState


def test_checkpoint():

    state = WorkflowState(
        query="Apple",
    )

    state.finish(
        "planner",
    )

    state.finish(
        "retriever",
    )

    checkpoint = WorkflowCheckpoint(
        state=state,
    )

    assert checkpoint.completed_steps == 2