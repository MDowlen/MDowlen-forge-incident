from datetime import datetime, timezone

from forge_incident.correlation import correlate
from forge_incident.models import Severity, Signal, SignalKind


def test_correlate_groups_nearby_service_signals():
    base = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    signals = [
        Signal(kind=SignalKind.metric, timestamp=base, service="checkout", message="latency high", value=950),
        Signal(kind=SignalKind.log, timestamp=base.replace(minute=2), service="checkout", message="timeout error"),
    ]
    events = correlate(signals)
    assert len(events) == 1
    assert events[0].service == "checkout"
    assert events[0].severity == Severity.high
    assert len(events[0].evidence) == 2
