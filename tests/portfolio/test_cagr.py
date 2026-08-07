from app.portfolio.cagr import CAGR


def test_cagr():

    cagr = CAGR()

    assert cagr.calculate(
        100,
        200,
        5,
    ) > 0