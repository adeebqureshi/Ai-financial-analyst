"""
Piotroski F-Score model.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PiotroskiScore:
    """
    Represents a Piotroski F-Score.
    """

    score: int

    @property
    def rating(self) -> str:

        if self.score >= 8:
            return "Strong"

        if self.score >= 5:
            return "Average"

        return "Weak"