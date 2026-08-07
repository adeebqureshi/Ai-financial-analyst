from app.workflow.node import WorkflowNode
from app.workflow.state import WorkflowState


def test_node():

    node = WorkflowNode(
        name="planner",
    )

    state = WorkflowState(
        query="Apple",
    )

    result = node.run(
        state,
    )

    assert result.completed == [
        "planner",
    ]