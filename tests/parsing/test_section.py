from app.parsing.section import Section


def test_word_count():

    section = Section(
        title="Revenue",
        content="Revenue increased significantly",
    )

    assert section.word_count == 3