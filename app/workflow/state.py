"""
Workflow state.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class WorkflowState:
    """
    Shared workflow state.
    """

    query: str

    data: dict[str, object] = field(default_factory=dict)

    completed: list[str] = field(default_factory=list)

    def set(
        self,
        key: str,
        value: object,
    ) -> None:

        self.data[key] = value

    def get(
        self,
        key: str,
        default: object | None = None,
    ) -> object | None:

        return self.data.get(
            key,
            default,
        )

    def finish(
        self,
        node: str,
    ) -> None:

        self.completed.append(node)