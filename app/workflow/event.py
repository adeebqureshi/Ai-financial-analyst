"""
Workflow event.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class WorkflowEvent:
    """
    Event emitted during execution.
    """

    node: str

    message: str