from app.infrastructure.environment import Environment


def test_environment():
    env = Environment()
    assert env.settings.environment in {
        "development",
        "production",
        "test",
        "staging",
    }
    assert isinstance(env.is_development, bool)
    assert isinstance(env.is_production, bool)
    assert not (env.is_development and env.is_production)
    assert env.is_development == (env.settings.environment == "development")
    assert env.is_production == (env.settings.environment == "production")
