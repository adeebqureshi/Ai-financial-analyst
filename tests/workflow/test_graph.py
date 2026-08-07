from app.workflow.graph import WorkflowGraph
from app.workflow.node import WorkflowNode
from app.workflow.state import WorkflowState


def test_graph():

    graph = WorkflowGraph()

    graph.add_node(
        WorkflowNode("planner"),
    )

    graph.add_node(
        WorkflowNode("retriever"),
    )

    state = graph.run(
        WorkflowState(
            query="Apple",
        )
    )

    assert state.completed == [
        "planner",
        "retriever",
    ]