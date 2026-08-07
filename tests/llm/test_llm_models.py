from app.llm.models import LLMRequest, LLMResponse


def test_llm_models():

    request = LLMRequest(
        prompt="Hello"
    )

    response = LLMResponse(
        text="World",
        model="mock",
    )

    assert request.prompt == "Hello"
    assert response.text == "World"
    assert response.model == "mock"