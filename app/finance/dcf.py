"""
Discounted Cash Flow model.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class DCFValuation:
    """
    Result of a DCF valuation.
    """

    enterprise_value: float
    equity_value: float
    intrinsic_value_per_share: float