"""
Task model.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Task:
    """
    Represents a task assigned to an agent.
    """

    name: str
    description: str

    @property
    def short_name(self) -> str:
        return self.name.lower().replace(" ", "_")