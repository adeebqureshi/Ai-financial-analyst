from app.llm.tokenizer import Tokenizer


def test_count():

    assert Tokenizer.count("hello world") == 2


def test_empty():

    assert Tokenizer.count("") == 0