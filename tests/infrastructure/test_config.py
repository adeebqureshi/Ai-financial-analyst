from app.infrastructure.config import Settings


def test_config():

    settings = Settings()

    assert settings.app_name

    assert settings.port > 0