"""
SEC company model.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SECCompany:

    cik: str

    ticker: str

    title: str