from app.parsers.section_parser import SectionParser


TEXT = """
ITEM 1. Business

Apple designs consumer electronics.

ITEM 1A. Risk Factors

Competition is intense.

ITEM 7. Management's Discussion and Analysis

Revenue increased significantly.

ITEM 8. Financial Statements

Balance Sheet...
"""


def test_split_sections():

    parser = SectionParser()

    sections = parser.split(TEXT)

    assert len(sections) == 4

    assert any("BUSINESS" in key for key in sections)

    assert any("RISK" in key for key in sections)

    assert any("MANAGEMENT" in key for key in sections)

    assert any("FINANCIAL" in key for key in sections)