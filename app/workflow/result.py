"""
Workflow result.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.workflow.state import WorkflowState


@dataclass(slots=True)
class WorkflowResult:
    """
    Final workflow result.
    """

    state: WorkflowState

    success: bool

    @property
    def completed_steps(self) -> int:
        return len(self.state.completed)