from app.infrastructure.environment import Environment


def test_environment():
    env = Environment()
    # ENVIRONMENT can be development, production, or test/staging in CI.
    assert env.settings.environment in {
        "development",
        "production",
        "test",
        "staging",
    }
    assert isinstance(env.is_development, bool)
    assert isinstance(env.is_production, bool)
    # Properties must be mutually exclusive and match the raw setting.
    assert not (env.is_development and env.is_production)
    assert env.is_development == (env.settings.environment == "development")
    assert env.is_production == (env.settings.environment == "production")