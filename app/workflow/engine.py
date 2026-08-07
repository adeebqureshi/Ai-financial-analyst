"""
Workflow engine.
"""

from __future__ import annotations

from app.workflow.executor import WorkflowExecutor
from app.workflow.pipeline import WorkflowPipeline
from app.workflow.result import WorkflowResult


class WorkflowEngine:

    def __init__(self) -> None:

        self.pipeline = WorkflowPipeline()

    def run(
        self,
        query: str,
    ) -> WorkflowResult:

        graph = self.pipeline.build()

        executor = WorkflowExecutor(
            graph,
        )

        state = executor.execute(
            query,
        )

        return WorkflowResult(
            state=state,
            success=True,
        )