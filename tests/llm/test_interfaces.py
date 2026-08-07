from app.llm.interfaces import LLMProvider
from app.llm.models import LLMRequest
from app.llm.models import LLMResponse


class DummyProvider(LLMProvider):

    def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:

        return LLMResponse(
            text=request.prompt,
            model="dummy",
        )


def test_provider():

    provider = DummyProvider()

    response = provider.generate(
        LLMRequest(
            prompt="hello",
        )
    )

    assert response.text == "hello"
    assert response.model == "dummy"