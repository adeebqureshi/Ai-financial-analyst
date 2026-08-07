from app.llm.prompt_builder import PromptBuilder


def test_prompt():

    prompt = PromptBuilder.build(
        query="Should I buy Apple?",
        context="Apple revenue increased.",
        report="Intrinsic value is 250.",
    )

    assert "Should I buy Apple?" in prompt
    assert "Apple revenue increased." in prompt
    assert "Intrinsic value is 250." in prompt
    assert "Do not hallucinate" in prompt