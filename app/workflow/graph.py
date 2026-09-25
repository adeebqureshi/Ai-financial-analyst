from __future__ import annotations

from app.core.exceptions import ValidationError
from app.workflow.node import WorkflowNode
from app.workflow.state import WorkflowState


DEFAULT_MAX_WORKFLOW_DEPTH = 10


class WorkflowGraph:
    def __init__(self, max_depth: int = DEFAULT_MAX_WORKFLOW_DEPTH) -> None:
        if max_depth < 1:
            raise ValueError("max_depth must be at least 1")
        self.max_depth = max_depth
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
            if state.depth >= self.max_depth:
                raise ValidationError(
                    "Workflow execution exceeded the maximum depth.",
                    error_code="WORKFLOW_MAX_DEPTH_EXCEEDED",
                    details={"max_depth": self.max_depth},
                )
            state.depth += 1
            state = node.run(state)
        return state
