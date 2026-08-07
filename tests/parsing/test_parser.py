from app.ingestion.document import FinancialDocument
from app.ingestion.metadata import DocumentMetadata
from app.parsing.parser import DocumentParser


def test_parser():

    document = FinancialDocument(
        text="""
# Revenue

Revenue increased.

# Net Income

Net income increased.
""",
        metadata=DocumentMetadata(
            source="test",
            filename="sample.txt",
        ),
    )

    parser = DocumentParser()

    sections = parser.parse(document)

    assert len(sections) == 2

    assert sections[0].title == "Revenue"

    assert sections[1].title == "Net Income"