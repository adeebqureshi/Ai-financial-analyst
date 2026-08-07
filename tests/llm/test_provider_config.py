from app.llm.provider_config import ProviderConfig


def test_defaults():

    config = ProviderConfig()

    assert config.provider == "mock"
    assert config.model == "gpt-4.1"
    assert config.temperature == 0.2
    assert config.max_tokens == 4096
    assert config.timeout == 60


def test_custom():

    config = ProviderConfig(
        provider="openai",
        model="gpt-5",
        temperature=0.7,
        max_tokens=2048,
        timeout=30,
    )

    assert config.provider == "openai"
    assert config.model == "gpt-5"
    assert config.temperature == 0.7
    assert config.max_tokens == 2048
    assert config.timeout == 30