"""
document_parser.py

Unified, layout-aware financial PDF parsing.

This module provides a single entry point for parsing financial PDFs
through a best-available-parser fallback chain::

    LlamaParse  (layout-aware Markdown, API key required)
        ↓ fallback
    Marker      (layout-aware Markdown, optional dependency)
        ↓ fallback
    PyMuPDF     (reliable plain-text fallback, never fabricates tables)

Design principles:
    - **Graceful degradation.** A missing optional dependency (LlamaParse /
      Marker) or a parse failure at one level silently falls through to the
      next parser. The upload pipeline therefore never crashes because an
      optional parser is unavailable.
    - **Observable failures.** Every skipped or failed parser is logged, and
      a total failure raises :class:`ParserError` with per-parser details —
      a failure is never silently treated as success.
    - **Reuse over duplication.** The PyMuPDF fallback reuses the existing
      :class:`app.ingestion.pdf_loader.PDFLoader`, and tables are extracted
      with the existing :class:`app.parsers.table_parser.TableParser`.
    - **Structure preservation.** Markdown tables produced by LlamaParse /
      Marker are turned into structured :class:`ParsedTable` objects, keeping
      columnar financial data (e.g. ``Revenue | COGS | Gross Profit``)
      associated instead of flattened into prose.
"""

from __future__ import annotations

import importlib.util
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from app.core.exceptions import ParserError
from app.core.logging import get_logger
from app.parsers.table_parser import ParsedTable, TableParser

logger = get_logger(__name__)

PARSER_LLAMAPARSE: Final[str] = "llamaparse"
PARSER_MARKER: Final[str] = "marker"
PARSER_PYMUPDF: Final[str] = "pymupdf"

_PAGE_MARKER = re.compile(r"(?m)^\s*[Pp]age\s+(\d+)\s*[:-]\s*")

_SUPPORTED_EXTENSIONS: Final[tuple[str, ...]] = (".pdf",)


@dataclass(slots=True)
class DocumentParseResult:
    """
    Canonical, parser-independent result of document parsing.

    Attributes:
        text: Full extracted text/Markdown.
        parser_used: Name of the parser that produced the result.
        pages: Optional page-split text (1-indexed by position). Best effort —
            structural page boundaries are only available for PyMuPDF and
            Markdown output that carries page markers.
        tables: Structured financial tables found in the source.
        filename: Source filename when known.
        warnings: Non-fatal observations (e.g. degraded page attribution).
    """

    text: str
    parser_used: str
    pages: list[str] = field(default_factory=list)
    tables: list[ParsedTable] = field(default_factory=list)
    filename: str | None = None
    warnings: list[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        """True when no text content was extracted."""
        return not self.text.strip()


class BaseDocumentParser(ABC):
    """Interface implemented by every parser in the fallback chain."""

    name: str = ""

    @abstractmethod
    def available(self) -> bool:
        """
        Whether this parser can currently be used.

        ``False`` for optional parsers whose package or credentials are
        missing; ``True`` alone does not guarantee a successful parse.
        """

    @abstractmethod
    def parse(
        self,
        path: str,
        filename: str | None = None,
    ) -> DocumentParseResult:
        """
        Parse a document from ``path``.

        Raises:
            ParserError: If parsing fails or produces no content. The caller
                (the fallback chain) is expected to continue to the next
                parser.
        """


# ──────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ──────────────────────────────────────────────────────────────────────────────


def _split_markdown_pages(markdown: str) -> list[str]:
    """
    Split LlamaParse/Marker Markdown on ``Page N:`` markers when present.

    Returns an empty list when no reliable page markers exist, letting
    callers fall back to treating the whole document as a single page.
    """
    matches = list(_PAGE_MARKER.finditer(markdown))

    if not matches:
        return []

    pages: list[str] = []

    prefix = markdown[: matches[0].start()].strip()

    if prefix:
        pages.append(prefix)

    for index, match in enumerate(matches):
        start = match.end()

        end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(markdown)
        )

        content = markdown[start:end].strip()

        if content:
            pages.append(content)

    return pages


def _tables_from_pages(pages: list[str]) -> list[ParsedTable]:
    """Extract tables page by page so each table records its page number."""
    tables: list[ParsedTable] = []

    parser = TableParser()

    for page_number, page_text in enumerate(pages, start=1):
        tables.extend(
            parser.parse_markdown(
                page_text,
                source_page=page_number,
            )
        )

    return tables


def _component_text(component: object) -> str:
    """Extract text from a LlamaParse document/component object."""
    text = getattr(component, "text", None)

    if isinstance(text, str):
        return text

    return str(component)


# ──────────────────────────────────────────────────────────────────────────────
# Concrete parsers
# ──────────────────────────────────────────────────────────────────────────────


class LlamaParseParser(BaseDocumentParser):
    """
    Layout-aware Markdown parsing via LlamaParse.

    Requires an ``LLAMA_PARSE_API_KEY`` and the optional ``llama-parse``
    package. When either is missing this parser reports itself unavailable
    and the fallback chain skips it.
    """

    name: str = PARSER_LLAMAPARSE

    def __init__(
        self,
        api_key: str | None = None,
    ) -> None:
        self._api_key = api_key or ""

    def available(self) -> bool:
        if not self._api_key:
            logger.debug("LlamaParse skipped: no API key configured.")
            return False

        if not _is_module_available("llama_parse"):
            logger.debug("LlamaParse skipped: optional dependency not installed.")
            return False

        return True

    def parse(
        self,
        path: str,
        filename: str | None = None,
    ) -> DocumentParseResult:
        if not self.available():
            raise ParserError(
                message=(
                    "LlamaParse is unavailable (missing API key or "
                    "the 'llama-parse' package)."
                ),
                error_code="PARSER_LLAMAPARSE_UNAVAILABLE",
            )

        try:
            markdown = self._extract(path)
        except ParserError:
            raise
        except Exception as exc:
            raise ParserError(
                message=f"LlamaParse failed to parse the document: {exc}",
                error_code="PARSER_LLAMAPARSE_FAILED",
                details={"filename": filename or Path(path).name},
            ) from exc

        if not markdown.strip():
            raise ParserError(
                message="LlamaParse returned an empty result.",
                error_code="PARSER_LLAMAPARSE_EMPTY",
            )

        pages = _split_markdown_pages(markdown)

        if not pages:
            pages = [markdown]

        return DocumentParseResult(
            text=markdown,
            parser_used=self.name,
            pages=pages,
            tables=_tables_from_pages(pages),
            filename=filename or Path(path).name,
        )

    def _extract(self, path: str) -> str:
        """
        Load the document through LlamaParse requesting Markdown output.

        The package's sync API surface has changed across releases, so both
        the modern ``load_data()`` reader interface and the legacy
        ``_load_file()`` job interface are attempted.
        """
        from llama_parse import LlamaParse

        parser = LlamaParse(
            api_key=self._api_key,
            result_type="markdown",
            verbose=False,
        )

        try:
            documents = parser.load_data(str(path))
        except Exception:
            job = parser._load_file(str(path))
            documents = job.result()

        return "\n\n".join(_component_text(document) for document in documents)


class MarkerParser(BaseDocumentParser):
    """
    Layout-aware Markdown parsing via the optional ``marker-pdf`` package.

    Marker requires local model artifacts that may be missing on fresh
    environments; when the package is installed but conversion fails, the
    fallback chain continues to PyMuPDF so ingestion is never blocked.
    """

    name: str = PARSER_MARKER

    def available(self) -> bool:
        return _is_module_available("marker")

    def parse(
        self,
        path: str,
        filename: str | None = None,
    ) -> DocumentParseResult:
        if not self.available():
            raise ParserError(
                message="Marker is not installed.",
                error_code="PARSER_MARKER_UNAVAILABLE",
            )

        try:
            markdown = self._convert(path)
        except ParserError:
            raise
        except Exception as exc:
            raise ParserError(
                message=f"Marker failed to parse the document: {exc}",
                error_code="PARSER_MARKER_FAILED",
                details={"filename": filename or Path(path).name},
            ) from exc

        if not markdown.strip():
            raise ParserError(
                message="Marker returned an empty result.",
                error_code="PARSER_MARKER_EMPTY",
            )

        pages = _split_markdown_pages(markdown)

        if not pages:
            pages = [markdown]

        return DocumentParseResult(
            text=markdown,
            parser_used=self.name,
            pages=pages,
            tables=_tables_from_pages(pages),
            filename=filename or Path(path).name,
        )

    @staticmethod
    def _convert(path: str) -> str:
        """
        Convert a PDF to Markdown with the Marker Python API.
        """
        from marker.converters.pdf import PdfConverter
        from marker.models import create_model_dict
        from marker.output import text_from_rendered

        converter = PdfConverter(
            artifact_dict=create_model_dict(),
        )

        rendered = converter(str(path))

        text, _, _ = text_from_rendered(rendered)

        return text


class PyMuPDFParser(BaseDocumentParser):
    """
    Reliable plain-text fallback using PyMuPDF.

    Reuses the existing :class:`app.ingestion.pdf_loader.PDFLoader`, keeps
    per-page text and never fabricates tables — table extraction only
    recognizes Markdown table syntax that is literally present in the text.
    """

    name: str = PARSER_PYMUPDF

    def available(self) -> bool:
        return _is_module_available("fitz")

    def parse(
        self,
        path: str,
        filename: str | None = None,
    ) -> DocumentParseResult:
        from app.ingestion.pdf_loader import PDFLoader

        try:
            document = PDFLoader().load(path)
        except ParserError:
            raise
        except Exception as exc:
            raise ParserError(
                message=f"PyMuPDF failed to parse the document: {exc}",
                error_code="PARSER_PYMUPDF_FAILED",
                details={"filename": filename or Path(path).name},
            ) from exc

        if not document.text.strip():
            raise ParserError(
                message="PyMuPDF extracted no text from the document.",
                error_code="PARSER_PYMUPDF_EMPTY",
                details={"filename": filename or Path(path).name},
            )

        return DocumentParseResult(
            text=document.text,
            parser_used=self.name,
            pages=list(document.pages) or [document.text],
            tables=_tables_from_pages(document.pages or [document.text]),
            filename=filename or document.metadata.filename,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Unified orchestration
# ──────────────────────────────────────────────────────────────────────────────


class UnifiedDocumentParser:
    """
    Best-available-parser orchestrator for financial PDFs.

    The parser chain is: LlamaParse → Marker → PyMuPDF. Each parser is only
    attempted when it reports itself available; any failure or empty result
    falls through to the next parser. If every parser fails, a controlled
    :class:`ParserError` is raised with per-parser failure details.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        parsers: list[BaseDocumentParser] | None = None,
    ) -> None:
        self._api_key = api_key

        self._parsers: list[BaseDocumentParser] = (
            parsers
            if parsers is not None
            else [
                LlamaParseParser(api_key=api_key),
                MarkerParser(),
                PyMuPDFParser(),
            ]
        )

    @property
    def parsers(self) -> list[BaseDocumentParser]:
        """The configured parser chain (new list every access)."""
        return list(self._parsers)

    def available_parsers(self) -> list[str]:
        """Names of parsers that currently report themselves available."""
        return [parser.name for parser in self._parsers if parser.available()]

    def parse(
        self,
        path: str | Path,
        filename: str | None = None,
    ) -> DocumentParseResult:
        """
        Parse a financial PDF using the best available parser.

        Raises:
            ParserError: If the file type is unsupported, the file is missing,
                or every available parser fails.
        """
        path_obj = Path(path)

        if not path_obj.exists():
            raise ParserError(
                message=f"Document file not found: {path_obj}",
                error_code="DOC_PARSE_NOT_FOUND",
                details={"filename": filename or path_obj.name},
            )

        if path_obj.suffix.lower() not in _SUPPORTED_EXTENSIONS:
            raise ParserError(
                message=(
                    "Unsupported file type. Only PDF documents are supported."
                ),
                error_code="DOC_PARSE_UNSUPPORTED_TYPE",
                details={
                    "filename": filename or path_obj.name,
                    "extension": path_obj.suffix,
                },
            )

        failures: list[dict[str, str]] = []

        document_name = filename or path_obj.name

        for parser in self._parsers:
            if not parser.available():
                logger.debug(
                    "Parser '%s' unavailable for '%s'; continuing down the chain.",
                    parser.name,
                    document_name,
                )
                continue

            try:
                result = parser.parse(str(path_obj), filename=filename)
            except ParserError as exc:
                logger.warning(
                    "Parser '%s' failed for '%s': %s",
                    parser.name,
                    document_name,
                    exc.message,
                )
                failures.append(
                    {
                        "parser": parser.name,
                        "error": exc.message,
                    }
                )
                continue
            except Exception as exc:  # noqa: BLE001 - defensive chain boundary
                logger.warning(
                    "Parser '%s' raised an unexpected error for '%s': %s",
                    parser.name,
                    document_name,
                    exc,
                )
                failures.append(
                    {
                        "parser": parser.name,
                        "error": str(exc),
                    }
                )
                continue

            if result.is_empty:
                logger.warning(
                    "Parser '%s' returned empty content for '%s'.",
                    parser.name,
                    document_name,
                )
                failures.append(
                    {
                        "parser": parser.name,
                        "error": "empty output",
                    }
                )
                continue

            logger.info(
                "Parsed '%s' with parser '%s' (%d page(s), %d table(s)).",
                document_name,
                parser.name,
                len(result.pages),
                len(result.tables),
            )

            return result

        raise ParserError(
            message=(
                "All document parsers failed; no content could be extracted "
                f"from '{document_name}'."
            ),
            error_code="DOC_PARSE_ALL_FAILED",
            details={
                "filename": document_name,
                "failures": failures,
            },
        )


# ──────────────────────────────────────────────────────────────────────────────
# Module helpers
# ──────────────────────────────────────────────────────────────────────────────


def _is_module_available(module_name: str) -> bool:
    """Return True when ``module_name`` can be imported."""
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, ValueError):
        return False