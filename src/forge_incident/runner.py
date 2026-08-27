from __future__ import annotations

from pathlib import Path

from .graph import build_graph
from .ingestion import load_incident
from .models import IncidentInput, IncidentReport, WorkflowState


def run_incident(incident: IncidentInput) -> IncidentReport:
    state = WorkflowState(incident=incident)
    result = build_graph().invoke(state)
    report = result.get("report") if isinstance(result, dict) else getattr(result, "report", None)
    if report is None:
        raise RuntimeError("Incident workflow completed without a report")
    return IncidentReport.model_validate(report)


def run_fixture(path: Path) -> IncidentReport:
    return run_incident(load_incident(path))
