from __future__ import annotations

from collections import Counter

from .models import CorrelatedEvent, EvidenceRef, RootCauseHypothesis, Severity, SignalKind


def diagnose(events: list[CorrelatedEvent], context_pack: dict | None) -> list[RootCauseHypothesis]:
    """Produce evidence-backed deterministic hypotheses before any optional model enrichment."""
    hypotheses: list[RootCauseHypothesis] = []
    all_signals = [signal for event in events for signal in event.signals]
    if not all_signals:
        return hypotheses

    service_counts = Counter(signal.service for signal in all_signals)
    deployments = [signal for signal in all_signals if signal.kind == SignalKind.deployment]
    errors = [
        signal
        for signal in all_signals
        if any(token in signal.message.lower() for token in ("error", "failed", "timeout", "5xx", "panic"))
    ]

    if deployments and errors:
        first_error = min(errors, key=lambda item: item.timestamp)
        nearby = [
            deployment
            for deployment in deployments
            if abs((first_error.timestamp - deployment.timestamp).total_seconds()) <= 900
        ]
        if nearby:
            evidence = [
                EvidenceRef(
                    source_type="deployment",
                    source=item.source or item.service,
                    detail=item.message,
                    score=1.0,
                )
                for item in nearby
            ]
            evidence.append(
                EvidenceRef(
                    source_type=first_error.kind.value,
                    source=first_error.source or first_error.service,
                    detail=first_error.message,
                    score=1.0,
                )
            )
            hypotheses.append(
                RootCauseHypothesis(
                    title="Recent deployment correlated with failure onset",
                    explanation=(
                        "A deployment occurred within 15 minutes of the first observed failure. "
                        "This is correlation, not proof, so rollback/compare evidence should be checked."
                    ),
                    confidence=0.82,
                    affected_services=sorted({item.service for item in nearby} | {first_error.service}),
                    evidence=evidence,
                    falsifiers=[
                        "The same errors began before the deployment.",
                        "Rollback does not improve the affected signals.",
                        "An independent dependency failed first.",
                    ],
                )
            )

    for event in events:
        metric_signals = [signal for signal in event.signals if signal.kind == SignalKind.metric]
        error_signals = [
            signal
            for signal in event.signals
            if any(token in signal.message.lower() for token in ("latency", "timeout", "error", "5xx"))
        ]
        if metric_signals and error_signals:
            hypotheses.append(
                RootCauseHypothesis(
                    title=f"{event.service} resource or latency saturation",
                    explanation=(
                        "Metric degradation and application errors occur in the same correlation window."
                    ),
                    confidence=0.67,
                    affected_services=[event.service],
                    evidence=event.evidence[:8],
                    falsifiers=[
                        "Resource/latency metrics remain normal during the failure window.",
                        "The service remains unhealthy after upstream dependencies recover.",
                    ],
                )
            )

    if not hypotheses:
        busiest = service_counts.most_common(1)[0][0]
        event = next(item for item in events if item.service == busiest)
        hypotheses.append(
            RootCauseHypothesis(
                title=f"Failure concentrated around {busiest}",
                explanation=(
                    "The strongest available evidence is concentrated on this service, but the current "
                    "signals do not establish a causal mechanism. Treat this as a triage lead."
                ),
                confidence=0.35,
                affected_services=[busiest],
                evidence=event.evidence[:8],
                falsifiers=["A different service shows an earlier causal signal."],
            )
        )

    # Ground one additional hypothesis in repository/runbook evidence when retrieval is strong.
    if context_pack:
        answer = context_pack.get("answer") or {}
        citations = answer.get("citations") or []
        confidence = float(answer.get("confidence", 0.0) or 0.0)
        if citations and confidence >= 0.25:
            evidence = [
                EvidenceRef(
                    source_type="repository",
                    source=str(item.get("path", "unknown")),
                    detail=(
                        f"lines {item.get('start_line', '?')}-{item.get('end_line', '?')}"
                        + (f" symbol {item.get('symbol')}" if item.get("symbol") else "")
                    ),
                    score=max(0.0, min(1.0, float(item.get("score", 0.0) or 0.0))),
                )
                for item in citations[:5]
            ]
            hypotheses.append(
                RootCauseHypothesis(
                    title="Repository/runbook evidence may explain the failure path",
                    explanation=str(answer.get("answer", "Grounded repository evidence was retrieved.")),
                    confidence=min(0.75, confidence),
                    affected_services=sorted(service_counts),
                    evidence=evidence,
                    falsifiers=["The cited code/runbook path is unrelated to the observed signals."],
                )
            )

    return sorted(hypotheses, key=lambda item: item.confidence, reverse=True)


def incident_severity(events: list[CorrelatedEvent]) -> Severity:
    order = {Severity.info: 0, Severity.warning: 1, Severity.high: 2, Severity.critical: 3}
    return max((event.severity for event in events), key=order.get, default=Severity.info)
