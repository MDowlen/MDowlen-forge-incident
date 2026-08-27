from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .models import IncidentInput, Signal


def load_incident(path: Path) -> IncidentInput:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return IncidentInput.model_validate(payload)


def normalize_signals(signals: list[Signal]) -> list[Signal]:
    normalized: list[Signal] = []
    for signal in signals:
        timestamp = signal.timestamp
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        else:
            timestamp = timestamp.astimezone(timezone.utc)
        normalized.append(signal.model_copy(update={"timestamp": timestamp}))
    return sorted(normalized, key=lambda item: item.timestamp)


def incident_window(signals: list[Signal]) -> tuple[datetime, datetime]:
    if not signals:
        now = datetime.now(timezone.utc)
        return now, now
    return signals[0].timestamp, signals[-1].timestamp
