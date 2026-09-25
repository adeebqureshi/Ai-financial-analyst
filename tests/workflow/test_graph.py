from app.core.exceptions import ValidationError
from app.workflow.graph import WorkflowGraph
from app.workflow.node import WorkflowNode
from app.workflow.state import WorkflowState


def test_graph() -> None:
    graph = WorkflowGraph()
    graph.add_node(WorkflowNode("planner"))
    graph.add_node(WorkflowNode("retriever"))
    state = graph.run(WorkflowState(query="Apple"))
    assert state.completed == ["planner", "retriever"]
    assert state.depth == 2


def test_max_depth_stops_actual_node_execution() -> None:
    graph = WorkflowGraph(max_depth=2)
    for name in ("one", "two", "three"):
        graph.add_node(WorkflowNode(name))
    state = WorkflowState(query="Apple")

    try:
        graph.run(state)
    except ValidationError as exc:
        assert exc.error_code == "WORKFLOW_MAX_DEPTH_EXCEEDED"
    else:
        raise AssertionError("workflow depth limit was not enforced")

    assert state.completed == ["one", "two"]
    assert state.depth == 2


def test_depth_is_per_workflow_execution() -> None:
    graph = WorkflowGraph(max_depth=1)
    graph.add_node(WorkflowNode("one"))
    first = graph.run(WorkflowState(query="first"))
    second = graph.run(WorkflowState(query="second"))
    assert first.depth == second.depth == 1
