"""
SEC filing metadata.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SECFiling:

    accession_number: str

    form: str

    filing_date: str

    primary_document: str