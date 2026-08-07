from app.parsing.classifier import SectionClassifier
from app.parsing.section import Section


def test_classifier():

    sections = [
        Section(
            title="Risk Factors",
            content="...",
        ),
        Section(
            title="Management Discussion and Analysis",
            content="...",
        ),
        Section(
            title="Balance Sheet",
            content="...",
        ),
        Section(
            title="Random Section",
            content="...",
        ),
    ]

    classifier = SectionClassifier()

    results = classifier.classify(sections)

    assert results[0].category == "Risk Factors"

    assert results[1].category == "MD&A"

    assert results[2].category == "Balance Sheet"

    assert results[3].category == "Other"