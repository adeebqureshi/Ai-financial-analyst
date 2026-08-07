from app.llm.message import AssistantMessage
from app.llm.message import SystemMessage
from app.llm.message import UserMessage


def test_system():

    m = SystemMessage("hello")

    assert m.role == "system"
    assert m.content == "hello"


def test_user():

    m = UserMessage("hello")

    assert m.role == "user"


def test_assistant():

    m = AssistantMessage("hello")

    assert m.role == "assistant"