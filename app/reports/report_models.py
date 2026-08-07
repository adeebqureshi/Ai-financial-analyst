"""
report_models.py

Report data models.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Report:

    title: str

    content: str

    ticker: str