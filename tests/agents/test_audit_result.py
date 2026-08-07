from app.agents.audit_result import AuditResult


def test_result():

    result = AuditResult(
        passed=True,
        issues=[],
    )

    assert result.passed

    assert result.issue_count == 0