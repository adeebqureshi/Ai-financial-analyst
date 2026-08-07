"""
schemas.py

Public API request and response models.
"""

from __future__ import annotations

from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    ticker: str
    query: str


class AnalyzeResponse(BaseModel):
    ticker: str
    report: str