from __future__ import annotations
from dataclasses import dataclass
from app.workflow.state import WorkflowState
@dataclass(slots=True)
class WorkflowCheckpoint:
    state: WorkflowState
    @property
    def completed_steps(self) -> int:
        return len(self.state.completed)