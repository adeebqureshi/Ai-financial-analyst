"""
Workflow executor.
"""

from __future__ import annotations

from app.workflow.graph import WorkflowGraph
from app.workflow.state import WorkflowState


class WorkflowExecutor:
    """
    Executes a workflow graph.
    """

    def __init__(
        self,
        graph: WorkflowGraph,
    ) -> None:

        self.graph = graph

    def execute(
        self,
        query: str,
    ) -> WorkflowState:

        state = WorkflowState(
            query=query,
        )

        return self.graph.run(state)