"""
Live stock quote.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class StockQuote:

    symbol: str

    price: float

    previous_close: float

    change: float

    change_percent: float