from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class SignalKind(StrEnum):
    log = "log"
    metric = "metric"
    trace = "trace"
    deployment = "deployment"
    alert = "alert"


class Severity(StrEnum):
    info = "info"
    warning = "warning"
    high = "high"
    critical = "critical"


class IncidentStatus(StrEnum):
    investigating = "investigating"
    mitigated = "mitigated"
    resolved = "resolved"


class Signal(BaseModel):
    kind: SignalKind
    timestamp: datetime
    service: str
    message: str
    value: float | None = None
    unit: str | None = None
    labels: dict[str, str] = Field(default_factory=dict)
    source: str | None = None


class EvidenceRef(BaseModel):
    source_type: str
    source: str
    detail: str
    score: float = Field(default=0.0, ge=0.0, le=1.0)


class CorrelatedEvent(BaseModel):
    service: str
    summary: str
    severity: Severity
    start_time: datetime
    end_time: datetime
    signals: list[Signal]
    evidence: list[EvidenceRef] = Field(default_factory=list)


class RootCauseHypothesis(BaseModel):
    title: str
    explanation: str
    confidence: float = Field(ge=0.0, le=1.0)
    affected_services: list[str] = Field(default_factory=list)
    evidence: list[EvidenceRef] = Field(default_factory=list)
    falsifiers: list[str] = Field(default_factory=list)


class RemediationStep(BaseModel):
    action: str
    rationale: str
    risk: Severity = Severity.warning
    verification: str
    requires_human_approval: bool = True


class IncidentReport(BaseModel):
    incident_id: str
    status: IncidentStatus = IncidentStatus.investigating
    title: str
    summary: str
    severity: Severity
    started_at: datetime
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    affected_services: list[str]
    correlated_events: list[CorrelatedEvent]
    hypotheses: list[RootCauseHypothesis]
    remediation: list[RemediationStep]
    context: dict[str, Any] = Field(default_factory=dict)


class IncidentInput(BaseModel):
    incident_id: str
    title: str = "Operational incident"
    repo_path: str = "."
    signals: list[Signal]


class WorkflowState(BaseModel):
    incident: IncidentInput
    normalized_signals: list[Signal] = Field(default_factory=list)
    correlated_events: list[CorrelatedEvent] = Field(default_factory=list)
    context_pack: dict[str, Any] | None = None
    hypotheses: list[RootCauseHypothesis] = Field(default_factory=list)
    remediation: list[RemediationStep] = Field(default_factory=list)
    report: IncidentReport | None = None
