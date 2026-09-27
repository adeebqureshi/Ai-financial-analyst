
from __future__ import annotations


class IngestionError(Exception):
        pass


class UnsupportedDocumentError(IngestionError):
        pass


class DocumentParseError(IngestionError):
        pass


class DocumentNotFoundError(IngestionError):
        pass
