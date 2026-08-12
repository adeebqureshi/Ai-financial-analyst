"""
Tests for the unified document parser and its fallback chain.

External parsers (LlamaParse, Marker) are always mocked or reported
unavailable; CI never makes real API calls.
"""

from __future__ import annotations

import io
import uuid
from pathlib import Path

import fitz
import pytest

from app.core.exceptions import ParserError
from app.ingestion.document import FinancialDocument
from app.ingestion.document_parser import (
    BaseDocumentParser,
    DocumentParseResult,
    LlamaParseParser,
    MarkerParser,
    PyMuPDFParser,
    UnifiedDocumentParser,
)

_CONFIDENTIAL_MARKDOWN = (
    "# Income Statement\n\n"
    "| Revenue | COGS | Gross Profit |\n"
    "|---|---|---|\n"
    "| 500 | 200 | 300 |\n"
    "\nPage 2:\n\n"
    "| Cash | Total Liabilities |\n"
    "|---|---|\n"
    "| 1,250,000 | (500) |\n"
)


def _make_pdf(pages: list[str]) -> bytes:
    """Render a multi-page PDF in memory."""
    doc = fitz.open()

    for text in pages:
        page = doc.new_page()
        page.insert_text((72, 72), text)

    buffer = io.BytesIO()

    doc.save(buffer)

    doc.close()

    return buffer.getvalue()


def _write_pdf(tmp_path: Path, name: str, pages: list[str]) -> Path:
    path = tmp_path / f"{name}_{uuid.uuid4().hex[:8]}.pdf"
    path.write_bytes(_make_pdf(pages))
    return path


class _EmptyParser(BaseDocumentParser):
    name: str = "empty"

    def available(self) -> bool:
        return True

    def parse(
        self,
        path: str,
        filename: str | None = None,
    ) -> DocumentParseResult:
        return DocumentParseResult(text="", parser_used=self.name)


class _BrokenParser(BaseDocumentParser):
    name: str = "broken"

    def available(self) -> bool:
        return True

    def parse(
        self,
        path: str,
        filename: str | None = None,
    ) -> DocumentParseResult:
        raise ParserError(
            message="deliberate failure",
            error_code="PARSER_BROKEN",
        )


# ──────────────────────────────────────────────────────────────────────────────
# Availability gates
# ──────────────────────────────────────────────────────────────────────────────


def test_llamaparse_unavailable_without_api_key() -> None:
    parser = LlamaParseParser(api_key="")

    assert parser.available() is False


def test_llamaparse_unavailable_without_package(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.ingestion.document_parser._is_module_available",
        lambda module_name: False,
    )

    parser = LlamaParseParser(api_key="llx-test-key")

    assert parser.available() is False


def test_default_chain_reports_only_pymupdf_available() -> None:
    # In CI the optional LlamaParse/Marker packages are absent, so the
    # default chain must still expose PyMuPDF.
    unified = UnifiedDocumentParser(api_key="")

    available = unified.available_parsers()

    assert "llamaparse" not in available

    assert "pymupdf" in available


# ──────────────────────────────────────────────────────────────────────────────
# Fallback chain behavior
# ──────────────────────────────────────────────────────────────────────────────


def test_llamaparse_success(monkeypatch, tmp_path) -> None:
    pdf_path = _write_pdf(tmp_path, "apple", ["placeholder"])

    monkeypatch.setattr(
        LlamaParseParser,
        "available",
        lambda self: True,
    )
    monkeypatch.setattr(
        LlamaParseParser,
        "_extract",
        lambda self, path: _CONFIDENTIAL_MARKDOWN,
    )

    unified = UnifiedDocumentParser(api_key="llx-test-key")

    result = unified.parse(pdf_path, filename="apple_10k.pdf")

    assert result.parser_used == "llamaparse"

    assert len(result.tables) == 2

    assert result.tables[0].headers == ["Revenue", "COGS", "Gross Profit"]

    assert result.tables[0].rows == [["500", "200", "300"]]

    assert result.tables[0].source_page == 1

    assert result.tables[1].rows == [["1,250,000", "(500)"]]

    assert result.tables[1].source_page == 2


def test_llamaparse_failure_falls_back_to_marker(monkeypatch, tmp_path) -> None:
    pdf_path = _write_pdf(tmp_path, "apple", ["placeholder"])

    def failing_extract(self, path: str) -> str:
        raise ParserError(
            message="LlamaParse quota exceeded",
            error_code="PARSER_LLAMAPARSE_FAILED",
        )

    monkeypatch.setattr(LlamaParseParser, "available", lambda self: True)
    monkeypatch.setattr(LlamaParseParser, "_extract", failing_extract)
    monkeypatch.setattr(MarkerParser, "available", lambda self: True)
    monkeypatch.setattr(
        MarkerParser,
        "_convert",
        staticmethod(lambda path: _CONFIDENTIAL_MARKDOWN),
    )

    unified = UnifiedDocumentParser(api_key="llx-test-key")

    result = unified.parse(pdf_path, filename="apple_10k.pdf")

    assert result.parser_used == "marker"

    assert len(result.tables) == 2


def test_marker_failure_falls_back_to_pymupdf(monkeypatch, tmp_path) -> None:
    pdf_path = _write_pdf(tmp_path, "apple", ["Revenue increased 25%."])

    def failing_convert(path: str) -> str:
        raise RuntimeError("model artifacts missing")

    monkeypatch.setattr(MarkerParser, "available", lambda self: True)
    monkeypatch.setattr(MarkerParser, "_convert", failing_convert)

    unified = UnifiedDocumentParser(api_key="")

    result = unified.parse(pdf_path, filename="apple_10k.pdf")

    assert result.parser_used == "pymupdf"

    assert "Revenue" in result.text


def test_pymupdf_fallback_without_optional_parsers(tmp_path) -> None:
    pdf_path = _write_pdf(tmp_path, "apple", ["Gross profit was 300."])

    unified = UnifiedDocumentParser(api_key="")

    result = unified.parse(pdf_path, filename="apple_10k.pdf")

    assert result.parser_used == "pymupdf"

    assert len(result.pages) >= 1

    assert "Gross profit" in result.text


def test_empty_output_falls_back_to_next_parser(tmp_path) -> None:
    pdf_path = _write_pdf(tmp_path, "apple", ["Real content from pymupdf."])

    unified = UnifiedDocumentParser(
        parsers=[
            _EmptyParser(),
            PyMuPDFParser(),
        ]
    )

    result = unified.parse(pdf_path, filename="apple_10k.pdf")

    assert result.parser_used == "pymupdf"


def test_complete_parser_failure_raises(tmp_path) -> None:
    pdf_path = _write_pdf(tmp_path, "apple", ["content"])

    unified = UnifiedDocumentParser(
        parsers=[
            _BrokenParser(),
            _BrokenParser(),
        ]
    )

    with pytest.raises(ParserError) as excinfo:
        unified.parse(pdf_path)

    assert excinfo.value.error_code == "DOC_PARSE_ALL_FAILED"

    assert len(excinfo.value.details["failures"]) == 2


def test_unsupported_file_type_raises(tmp_path) -> None:
    txt_path = tmp_path / "notes.txt"
    txt_path.write_text("hello", encoding="utf-8")

    unified = UnifiedDocumentParser(api_key="")

    with pytest.raises(ParserError) as excinfo:
        unified.parse(txt_path)

    assert excinfo.value.error_code == "DOC_PARSE_UNSUPPORTED_TYPE"


def test_missing_file_raises(tmp_path) -> None:
    unified = UnifiedDocumentParser(api_key="")

    with pytest.raises(ParserError) as excinfo:
        unified.parse(tmp_path / "missing.pdf")

    assert excinfo.value.error_code == "DOC_PARSE_NOT_FOUND"


# ──────────────────────────────────────────────────────────────────────────────
# PyMuPDF parsing details
# ──────────────────────────────────────────────────────────────────────────────


def test_pymupdf_parser_extracts_financial_table(tmp_path) -> None:
    pdf_path = _write_pdf(
        tmp_path,
        "financials",
        [
            "CONSOLIDATED STATEMENT OF OPERATIONS\n"
            "Revenue | COGS | Gross Profit\n"
            "500 | 200 | 300"
        ],
    )

    result = PyMuPDFParser().parse(str(pdf_path))

    assert result.parser_used == "pymupdf"

    assert len(result.tables) == 1

    table = result.tables[0]

    assert table.headers == ["Revenue", "COGS", "Gross Profit"]

    assert table.rows == [["500", "200", "300"]]

    assert table.source_page == 1

    assert table.title == "CONSOLIDATED STATEMENT OF OPERATIONS"


def test_pymupdf_parser_uses_existing_loader(tmp_path, monkeypatch) -> None:
    pdf_path = _write_pdf(tmp_path, "apple", ["page one text"])

    from app.ingestion.metadata import DocumentMetadata

    calls: list[str] = []

    def fake_load(self, path: str) -> FinancialDocument:
        calls.append(path)
        return FinancialDocument(
            text="page one text",
            metadata=DocumentMetadata(
                source="pdf",
                filename=Path(path).name,
            ),
            pages=["page one text"],
        )

    monkeypatch.setattr(
        "app.ingestion.pdf_loader.PDFLoader.load",
        fake_load,
    )

    result = PyMuPDFParser().parse(str(pdf_path))

    assert len(calls) == 1

    assert result.parser_used == "pymupdf"

    assert result.text == "page one text"