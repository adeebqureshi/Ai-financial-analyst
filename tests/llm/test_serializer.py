from app.llm.message import UserMessage
from app.llm.serializer import MessageSerializer


def test_dict():

    msg = UserMessage("hello")

    data = MessageSerializer.to_dict(msg)

    assert data["role"] == "user"

    assert data["content"] == "hello"


def test_list():

    data = MessageSerializer.to_list(
        [
            UserMessage("a"),
            UserMessage("b"),
        ]
    )

    assert len(data) == 2