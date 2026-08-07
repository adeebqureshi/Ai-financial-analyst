"""
Altman Z-Score model.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AltmanZScore:
    """
    Altman Z-Score result.
    """

    score: float

    @property
    def zone(self) -> str:

        if self.score > 2.99:
            return "Safe"

        if self.score >= 1.81:
            return "Grey"

        return "Distress"