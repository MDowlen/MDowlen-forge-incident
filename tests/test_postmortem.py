from datetime import datetime, timezone

from forge_incident.models import IncidentReport, Severity
from forge_incident.postmortem import render_markdown


def test_postmortem_contains_core_sections():
    report = IncidentReport(
        incident_id="INC-1",
        title="Test incident",
        summary="summary",
        severity=Severity.high,
        started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        affected_services=["api"],
        correlated_events=[],
        hypotheses=[],
        remediation=[],
    )
    text = render_markdown(report)
    assert "# INC-1: Test incident" in text
    assert "## Root-cause hypotheses" in text
    assert "## Mitigation / remediation plan" in text
