from app.infrastructure.shutdown import shutdown
from app.infrastructure.startup import startup


def test_shutdown():

    container = startup()

    shutdown(container)