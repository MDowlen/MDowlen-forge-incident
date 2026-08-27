from __future__ import annotations

from pathlib import Path

from .context import OperationalContext
from .correlation import correlate
from .diagnosis import diagnose, incident_severity
from .ingestion import incident_window, normalize_signals
from .models import IncidentReport, WorkflowState
from .remediation import plan_remediation


def normalize_agent(state: WorkflowState) -> dict:
    return {"normalized_signals": normalize_signals(state.incident.signals)}


def correlation_agent(state: WorkflowState) -> dict:
    return {"correlated_events": correlate(state.normalized_signals)}


def context_agent(state: WorkflowState) -> dict:
    services = sorted({signal.service for signal in state.normalized_signals})
    kinds = sorted({signal.kind.value for signal in state.normalized_signals})
    question = (
        "Operational incident affecting services "
        f"{', '.join(services) or 'unknown'} with signals {', '.join(kinds) or 'unknown'}. "
        "Find relevant failure-handling code, runbooks, architecture decisions, retry/timeout behavior, "
        "and prior incident/postmortem documentation that could explain the observed symptoms."
    )
    try:
        pack = OperationalContext().pack(Path(state.incident.repo_path), question)
    except Exception as exc:
        pack = {"error": str(exc), "answer": {"confidence": 0.0, "citations": []}}
    return {"context_pack": pack}


def diagnosis_agent(state: WorkflowState) -> dict:
    return {"hypotheses": diagnose(state.correlated_events, state.context_pack)}


def remediation_agent(state: WorkflowState) -> dict:
    return {"remediation": plan_remediation(state.hypotheses)}


def report_agent(state: WorkflowState) -> dict:
    start, _ = incident_window(state.normalized_signals)
    services = sorted({signal.service for signal in state.normalized_signals})
    severity = incident_severity(state.correlated_events)
    top = state.hypotheses[0] if state.hypotheses else None
    summary = (
        f"Leading hypothesis: {top.title} ({top.confidence:.0%} confidence)."
        if top
        else "No evidence-backed root-cause hypothesis is available yet."
    )
    report = IncidentReport(
        incident_id=state.incident.incident_id,
        title=state.incident.title,
        summary=summary,
        severity=severity,
        started_at=start,
        affected_services=services,
        correlated_events=state.correlated_events,
        hypotheses=state.hypotheses,
        remediation=state.remediation,
        context=state.context_pack or {},
    )
    return {"report": report}
