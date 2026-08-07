from app.finance.beneish_engine import BeneishEngine


def test_engine():

    engine = BeneishEngine()

    result = engine.calculate(
        dsri=1.1,
        gmi=1.0,
        aqi=1.0,
        sgi=1.2,
        depi=1.0,
        sgai=1.0,
        lvgi=1.0,
        tata=0.03,
    )

    assert isinstance(result.score, float)

    assert isinstance(
        result.likely_manipulator,
        bool,
    )