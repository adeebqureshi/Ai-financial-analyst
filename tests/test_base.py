from app.models.base import DomainModel


class Dummy(DomainModel):

    name: str


def test_domain_model():

    obj = Dummy(
        name="Apple"
    )

    assert obj.name == "Apple"

    assert obj.created_at is not None