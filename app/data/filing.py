"""
SEC filing model.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Filing:

    accession_number: str

    filing_type: str

    company: str

    filing_date: str

    url: str