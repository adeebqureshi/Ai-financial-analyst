from __future__ import annotations

from dataclasses import dataclass

from app.portfolio.holding import Holding


@dataclass(slots=True)
class Portfolio:

    holdings: list[Holding]

    @property
    def total_value(self) -> float:

        return sum(
            h.value
            for h in self.holdings
        )