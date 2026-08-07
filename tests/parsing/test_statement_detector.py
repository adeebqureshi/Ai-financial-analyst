from app.parsing.section import Section
from app.parsing.statement_detector import StatementDetector


def test_detector():

    sections = [
        Section(
            title="Business Overview",
            content="Overview",
        ),
        Section(
            title="Balance Sheet",
            content="Assets",
        ),
        Section(
            title="Cash Flow Statement",
            content="Cash",
        ),
    ]

    detector = StatementDetector()

    statements = detector.detect(sections)

    assert len(statements) == 2

    assert statements[0].name == "Balance Sheet"

    assert statements[1].name == "Cash Flow Statement"