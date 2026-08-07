from app.llm.context import ContextWindow
from app.llm.message import UserMessage


def test_trim():

    ctx = ContextWindow(max_tokens=3)

    messages = [
        UserMessage("one two"),
        UserMessage("three"),
        UserMessage("four five"),
    ]

    trimmed = ctx.trim(messages)

    assert len(trimmed) == 2
    assert trimmed[0].content == "three"
    assert trimmed[1].content == "four five"