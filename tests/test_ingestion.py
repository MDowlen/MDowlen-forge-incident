from datetime import datetime, timezone

from forge_incident.ingestion import normalize_signals
from forge_incident.models import Signal, SignalKind


def test_normalize_signals_sorts_and_adds_timezone():
    signals = [
        Signal(kind=SignalKind.log, timestamp=datetime(2026, 1, 1, 12, 5), service="api", message="later"),
        Signal(kind=SignalKind.log, timestamp=datetime(2026, 1, 1, 12, 0), service="api", message="first"),
    ]
    normalized = normalize_signals(signals)
    assert normalized[0].message == "first"
    assert normalized[0].timestamp.tzinfo == timezone.utc
