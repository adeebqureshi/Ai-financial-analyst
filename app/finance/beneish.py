"""
Beneish M-Score model.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class BeneishMScore:
    """
    Beneish M-Score result.
    """

    score: float

    @property
    def likely_manipulator(self) -> bool:
        return self.score > -1.78