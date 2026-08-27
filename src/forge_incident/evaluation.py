from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from .runner import run_incident
from .models import IncidentInput


class IncidentEvalCase(BaseModel):
    incident: IncidentInput
    expected_hypothesis_terms: list[str] = Field(default_factory=list)
    expected_services: list[str] = Field(default_factory=list)


class IncidentEvalResult(BaseModel):
    incident_id: str
    hypothesis_hit: bool
    service_recall: float
    evidence_coverage: float


class IncidentEvalReport(BaseModel):
    cases: int
    hypothesis_hit_rate: float
    mean_service_recall: float
    mean_evidence_coverage: float
    results: list[IncidentEvalResult]


def load_cases(path: Path) -> list[IncidentEvalCase]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw = payload.get("cases", payload) if isinstance(payload, dict) else payload
    return [IncidentEvalCase.model_validate(item) for item in raw]


def evaluate(cases: list[IncidentEvalCase]) -> IncidentEvalReport:
    results: list[IncidentEvalResult] = []
    for case in cases:
        report = run_incident(case.incident)
        hypothesis_text = " ".join(
            f"{item.title} {item.explanation}".lower() for item in report.hypotheses
        )
        expected_terms = [term.lower() for term in case.expected_hypothesis_terms]
        hypothesis_hit = not expected_terms or any(term in hypothesis_text for term in expected_terms)

        expected_services = set(case.expected_services)
        actual_services = set(report.affected_services)
        service_recall = (
            len(expected_services & actual_services) / len(expected_services)
            if expected_services
            else 1.0
        )

        hypotheses = report.hypotheses
        evidence_coverage = (
            sum(1 for item in hypotheses if item.evidence) / len(hypotheses)
            if hypotheses
            else 0.0
        )
        results.append(
            IncidentEvalResult(
                incident_id=case.incident.incident_id,
                hypothesis_hit=hypothesis_hit,
                service_recall=service_recall,
                evidence_coverage=evidence_coverage,
            )
        )

    count = len(results)
    return IncidentEvalReport(
        cases=count,
        hypothesis_hit_rate=(sum(item.hypothesis_hit for item in results) / count) if count else 0.0,
        mean_service_recall=(sum(item.service_recall for item in results) / count) if count else 0.0,
        mean_evidence_coverage=(sum(item.evidence_coverage for item in results) / count) if count else 0.0,
        results=results,
    )
