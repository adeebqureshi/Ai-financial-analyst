from app.data.filing_parser import FilingParser


def test_parser():

    parser = FilingParser()

    sections = parser.parse(
        "Business section.\n\nRisk section."
    )

    assert len(sections) == 2

    assert sections[0].title == "Section 1"