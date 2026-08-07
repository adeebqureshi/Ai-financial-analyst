from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Holding:

    ticker: str

    shares: float

    price: float

    @property
    def value(self) -> float:

        return self.shares * self.price