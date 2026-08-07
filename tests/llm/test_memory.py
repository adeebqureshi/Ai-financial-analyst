from app.llm.memory import ConversationMemory


def test_memory():

    memory = ConversationMemory()

    memory.add_system("system")

    memory.add_user("user")

    memory.add_assistant("assistant")

    assert len(memory.conversation) == 3


def test_clear():

    memory = ConversationMemory()

    memory.add_user("hello")

    memory.clear()

    assert len(memory.conversation) == 0