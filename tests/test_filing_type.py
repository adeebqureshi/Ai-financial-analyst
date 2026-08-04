from app.enums.filing_type import FilingType


def test_filing_types():

    assert FilingType.FORM_10K.value == "10-K"

    assert FilingType.FORM_10Q.value == "10-Q"

    assert FilingType.FORM_8K.value == "8-K"