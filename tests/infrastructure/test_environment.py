from app.infrastructure.environment import Environment


def test_environment():

    env = Environment()

    assert (
        env.is_development
        or env.is_production
    )