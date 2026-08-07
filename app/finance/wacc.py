"""
Weighted Average Cost of Capital model.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class WACC:

    cost_of_equity: float

    after_tax_cost_of_debt: float

    wacc: float