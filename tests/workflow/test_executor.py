from app.workflow.executor import WorkflowExecutor
from app.workflow.graph import WorkflowGraph
from app.workflow.node import WorkflowNode


def test_executor():

    graph = WorkflowGraph()

    graph.add_node(
        WorkflowNode("planner"),
    )

    graph.add_node(
        WorkflowNode("retriever"),
    )

    executor = WorkflowExecutor(
        graph,
    )

    state = executor.execute(
        "Apple",
    )

    assert state.completed == [
        "planner",
        "retriever",
    ]