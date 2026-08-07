"""
Company model.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Company:

    ticker: str

    name: str

    sector: str

    industry: str

    exchange: str