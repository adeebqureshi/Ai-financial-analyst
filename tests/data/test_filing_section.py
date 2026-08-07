from app.data.filing_section import FilingSection


def test_section():

    section = FilingSection(
        title="Business",
        content="Apple designs consumer electronics.",
    )

    assert section.word_count == 4