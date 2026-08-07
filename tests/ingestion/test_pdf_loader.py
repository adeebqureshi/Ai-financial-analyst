from pathlib import Path

import fitz

from app.ingestion.pdf_loader import PDFLoader


def test_pdf_loader(tmp_path):

    pdf_path = tmp_path / "sample.pdf"

    doc = fitz.open()

    page = doc.new_page()

    page.insert_text(
        (72, 72),
        "Revenue increased by 25 percent.",
    )

    doc.save(pdf_path)

    doc.close()

    loader = PDFLoader()

    document = loader.load(str(pdf_path))

    assert "Revenue" in document.text

    assert document.metadata.source == "pdf"

    assert document.metadata.filename == "sample.pdf"