from app.llm.conversation import Conversation
from app.llm.message import UserMessage


def test_add():

    c = Conversation()

    c.add(UserMessage("hello"))

    assert len(c) == 1


def test_clear():

    c = Conversation()

    c.add(UserMessage("hello"))

    c.clear()

    assert len(c) == 0