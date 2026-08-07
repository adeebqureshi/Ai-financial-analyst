import httpx

from app.llm.http_client import LLMHttpClient


def test_client():

    client = LLMHttpClient()

    assert isinstance(
        client.client,
        httpx.Client,
    )

    client.close()


def test_context_manager():

    with LLMHttpClient() as client:

        assert isinstance(
            client.client,
            httpx.Client,
        )