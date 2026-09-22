from __future__ import annotations
class IngestionError(Exception):
class UnsupportedDocumentError(IngestionError):
class DocumentParseError(IngestionError):
class DocumentNotFoundError(IngestionError):