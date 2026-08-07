"""
Workflow history.
"""

from __future__ import annotations


class WorkflowHistory:

    def __init__(self) -> None:

        self.events: list[str] = []

    def add(
        self,
        event: str,
    ) -> None:

        self.events.append(event)

    @property
    def count(self) -> int:

        return len(self.events)