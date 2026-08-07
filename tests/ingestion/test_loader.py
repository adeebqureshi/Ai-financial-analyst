from pathlib import Path

from app.ingestion.document import FinancialDocument
from app.ingestion.loader import DocumentLoader
from app.ingestion.metadata import DocumentMetadata


class DummyLoader(DocumentLoader):

    def load(
        self,
        path: str,
    ) -> FinancialDocument:

        return FinancialDocument(
            text=Path(path).read_text(),
            metadata=DocumentMetadata(
                source="dummy",
                filename=Path(path).name,
            ),
        )


def test_loader(tmp_path):

    file = tmp_path / "sample.txt"

    file.write_text("Revenue Growth")

    loader = DummyLoader()

    document = loader.load(str(file))

    assert document.word_count == 2