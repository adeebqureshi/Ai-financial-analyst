from app.llm.usage import TokenUsage


def test_total_tokens():

    usage = TokenUsage(
        prompt_tokens=100,
        completion_tokens=50,
    )

    assert usage.total_tokens == 150


def test_empty_usage():

    usage = TokenUsage()

    assert usage.total_tokens == 0