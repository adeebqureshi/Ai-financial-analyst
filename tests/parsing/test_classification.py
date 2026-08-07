from app.parsing.classification import SectionClassification


def test_confident():

    result = SectionClassification(
        section_title="Balance Sheet",
        category="Balance Sheet",
        confidence=0.95,
    )

    assert result.is_confident


def test_not_confident():

    result = SectionClassification(
        section_title="Random",
        category="Other",
        confidence=0.40,
    )

    assert not result.is_confident