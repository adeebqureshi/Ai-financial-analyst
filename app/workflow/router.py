"""
Workflow router.
"""

from __future__ import annotations

from app.workflow.node import WorkflowNode


class WorkflowRouter:
    """
    Stores workflow routes.
    """

    def __init__(self) -> None:

        self.routes: dict[str, WorkflowNode] = {}

    def register(
        self,
        node: WorkflowNode,
    ) -> None:

        self.routes[node.name] = node

    def get(
        self,
        name: str,
    ) -> WorkflowNode:

        return self.routes[name]