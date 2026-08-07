"""
Workflow node.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.workflow.state import WorkflowState


@dataclass(slots=True)
class WorkflowNode:
    """
    Base workflow node.
    """

    name: str

    def run(
        self,
        state: WorkflowState,
    ) -> WorkflowState:

        state.finish(self.name)

        return state