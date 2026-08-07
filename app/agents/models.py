"""
models.py

Agent models.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AgentTask:

    name: str

    description: str