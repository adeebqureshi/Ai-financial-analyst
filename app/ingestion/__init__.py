"""
Financial document ingestion package.
"""

from .document import FinancialDocument
from .metadata import DocumentMetadata

__all__ = [
    "FinancialDocument",
    "DocumentMetadata",
]