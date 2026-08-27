from __future__ import annotations

from collections import defaultdict
from datetime import timedelta

from .models import CorrelatedEvent, EvidenceRef, Severity, Signal, SignalKind


def _severity(signals: list[Signal]) -> Severity:
    text = " ".join(signal.message.lower() for signal in signals)
    if any(word in text for word in ("outage", "panic", "fatal", "unavailable", "data loss")):
        return Severity.critical
    if any(word in text for word in ("error", "failed", "timeout", "latency", "5xx")):
        return Severity.high
    if any(word in text for word in ("warning", "degraded", "retry", "saturation")):
        return Severity.warning
    return Severity.info


def correlate(signals: list[Signal], window_minutes: int = 5) -> list[CorrelatedEvent]:
    if not signals:
        return []

    grouped: dict[str, list[Signal]] = defaultdict(list)
    for signal in signals:
        grouped[signal.service].append(signal)

    events: list[CorrelatedEvent] = []
    window = timedelta(minutes=window_minutes)
    for service, service_signals in sorted(grouped.items()):
        service_signals = sorted(service_signals, key=lambda item: item.timestamp)
        cluster: list[Signal] = []
        for signal in service_signals:
            if cluster and signal.timestamp - cluster[-1].timestamp > window:
                events.append(_event(service, cluster))
                cluster = []
            cluster.append(signal)
        if cluster:
            events.append(_event(service, cluster))

    return sorted(events, key=lambda event: (event.start_time, event.service))


def _event(service: str, signals: list[Signal]) -> CorrelatedEvent:
    kinds = sorted({signal.kind.value for signal in signals})
    deployments = [signal for signal in signals if signal.kind == SignalKind.deployment]
    summary = f"{len(signals)} correlated signals across {', '.join(kinds)}"
    if deployments:
        summary += f"; {len(deployments)} deployment signal(s) in window"
    evidence = [
        EvidenceRef(
            source_type=signal.kind.value,
            source=signal.source or signal.service,
            detail=signal.message,
            score=1.0,
        )
        for signal in signals
    ]
    return CorrelatedEvent(
        service=service,
        summary=summary,
        severity=_severity(signals),
        start_time=signals[0].timestamp,
        end_time=signals[-1].timestamp,
        signals=signals,
        evidence=evidence,
    )
