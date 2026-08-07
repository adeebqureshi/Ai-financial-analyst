from app.agents.auditor import AuditorAgent


class DummyAnalysis:

    intrinsic_value = 250.0

    recommendation = "BUY"

    health_score = 95


def test_auditor():

    auditor = AuditorAgent()

    assert auditor.audit(
        DummyAnalysis()
    )