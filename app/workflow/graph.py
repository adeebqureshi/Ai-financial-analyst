"""
Workflow graph.
"""

from __future__ import annotations

from app.workflow.node import WorkflowNode
from app.workflow.state import WorkflowState


class WorkflowGraph:
    """
    Executes workflow nodes sequentially.
    """

    def __init__(self) -> None:

        self.nodes: list[WorkflowNode] = []

    def add_node(
        self,
        node: WorkflowNode,
    ) -> None:

        self.nodes.append(node)

    def run(
        self,
        state: WorkflowState,
    ) -> WorkflowState:

        for node in self.nodes:
            state = node.run(state)

        return state