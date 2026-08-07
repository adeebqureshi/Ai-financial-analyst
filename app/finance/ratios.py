"""
Financial ratio models.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class FinancialRatios:

    current_ratio: float

    debt_to_equity: float

    return_on_assets: float

    return_on_equity: float

    gross_margin: float

    operating_margin: float

    net_margin: float