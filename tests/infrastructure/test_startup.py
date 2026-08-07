from app.infrastructure.startup import startup


def test_startup():

    container = startup()

    assert container.database is not None