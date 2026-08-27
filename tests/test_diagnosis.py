from datetime import datetime, timedelta, timezone

from forge_incident.correlation import correlate
from forge_incident.diagnosis import diagnose
from forge_incident.models import Signal, SignalKind


def test_deployment_near_failure_creates_correlation_hypothesis():
    base = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    signals = [
        Signal(kind=SignalKind.deployment, timestamp=base, service="api", message="release v42 deployed", source="deployments/api"),
        Signal(kind=SignalKind.log, timestamp=base + timedelta(minutes=5), service="api", message="5xx error rate increased", source="logs/api"),
    ]
    hypotheses = diagnose(correlate(signals), None)
    assert hypotheses
    assert "deployment" in hypotheses[0].title.lower()
    assert hypotheses[0].evidence
    assert hypotheses[0].falsifiers
