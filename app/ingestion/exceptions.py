"""
Exceptions for document ingestion.
"""

from __future__ import annotations


class IngestionError(Exception):
    """Base ingestion exception."""


class UnsupportedDocumentError(IngestionError):
    """Unsupported document type."""


class DocumentParseError(IngestionError):
    """Document parsing failed."""


class DocumentNotFoundError(IngestionError):
    """Document not found."""