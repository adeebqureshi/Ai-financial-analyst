from app.workflow.node import WorkflowNode
from app.workflow.router import WorkflowRouter


def test_router():

    router = WorkflowRouter()

    node = WorkflowNode(
        "planner",
    )

    router.register(
        node,
    )

    assert router.get(
        "planner",
    ) is node