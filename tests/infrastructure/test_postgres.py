from app.infrastructure.postgres import PostgreSQLManager


def test_postgres():

    db = PostgreSQLManager()

    connection = db.connect()

    assert connection is not None

    connection.close()

    db.dispose()