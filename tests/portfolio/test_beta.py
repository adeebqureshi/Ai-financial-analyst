from app.portfolio.beta import Beta


def test_beta():

    beta = Beta()

    assert beta.calculate(
        0.2,
        0.1,
    ) == 2.0