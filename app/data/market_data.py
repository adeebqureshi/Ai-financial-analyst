"""
Market data model.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class MarketData:

    price: float

    market_cap: float

    pe_ratio: float

    eps: float

    volume: int