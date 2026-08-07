from app.llm.stream import TokenStream


def test_iteration():

    stream = TokenStream(
        ["Hello", " ", "World"]
    )

    assert list(stream) == [
        "Hello",
        " ",
        "World",
    ]


def test_collect():

    stream = TokenStream(
        ["Hello", " ", "World"]
    )

    assert stream.collect() == "Hello World"