from app.infrastructure.request_id import generate_request_id


def test_request_id():

    rid = generate_request_id()

    assert isinstance(
        rid,
        str,
    )

    assert len(rid) > 10