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
    text: str
    parser_used: str
    pages: list[str] = field(default_factory=list)
    tables: list[ParsedTable] = field(default_factory=list)
    filename: str | None = None
    warnings: list[str] = field(default_factory=list)
    @property
    def is_empty(self) -> bool:
        return not self.text.strip()
class BaseDocumentParser(ABC):
    name: str = ""
    @abstractmethod
    def available(self) -> bool:
    @abstractmethod
    def parse(
        self,
        path: str,
        filename: str | None = None,
    ) -> DocumentParseResult:
def _split_markdown_pages(markdown: str) -> list[str]:
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
    text = getattr(component, "text", None)
    if isinstance(text, str):
        return text
    return str(component)
class LlamaParseParser(BaseDocumentParser):
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
class UnifiedDocumentParser:
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
        return list(self._parsers)
    def available_parsers(self) -> list[str]:
        return [parser.name for parser in self._parsers if parser.available()]
    def parse(
        self,
        path: str | Path,
        filename: str | None = None,
    ) -> DocumentParseResult:
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
            except Exception as exc:
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
def _is_module_available(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, ValueError):
        return False