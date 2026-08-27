from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from pydantic import BaseModel, Field

from .models import CorrelatedEvent, EvidenceRef, RootCauseHypothesis


class AdvisorHypothesis(BaseModel):
    title: str
    explanation: str
    confidence: float = Field(ge=0.0, le=1.0)
    affected_services: list[str] = Field(default_factory=list)
    evidence_ids: list[int] = Field(default_factory=list)
    falsifiers: list[str] = Field(default_factory=list)


class AdvisorOutput(BaseModel):
    hypotheses: list[AdvisorHypothesis] = Field(default_factory=list)


def _catalog(events: list[CorrelatedEvent], context_pack: dict | None) -> list[EvidenceRef]:
    evidence: list[EvidenceRef] = []
    for event in events:
        evidence.extend(event.evidence)
    if context_pack:
        for item in (context_pack.get("answer") or {}).get("citations") or []:
            evidence.append(
                EvidenceRef(
                    source_type="repository",
                    source=str(item.get("path", "unknown")),
                    detail=f"lines {item.get('start_line', '?')}-{item.get('end_line', '?')}",
                    score=max(0.0, min(1.0, float(item.get("score", 0.0) or 0.0))),
                )
            )
    return evidence[:80]


def _schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "hypotheses": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "explanation": {"type": "string"},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        "affected_services": {"type": "array", "items": {"type": "string"}},
                        "evidence_ids": {"type": "array", "items": {"type": "integer", "minimum": 0}},
                        "falsifiers": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": [
                        "title",
                        "explanation",
                        "confidence",
                        "affected_services",
                        "evidence_ids",
                        "falsifiers",
                    ],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["hypotheses"],
        "additionalProperties": False,
    }


def _output_text(payload: dict[str, Any]) -> str:
    for item in payload.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text" and content.get("text"):
                return str(content["text"])
    return str(payload.get("output_text", ""))


def model_hypotheses(
    events: list[CorrelatedEvent],
    context_pack: dict | None,
    *,
    api_key: str | None = None,
    model: str | None = None,
    timeout_seconds: float = 35.0,
) -> list[RootCauseHypothesis]:
    """Optional OpenAI advisor. Returns [] when no key is configured or the request fails.

    The model may reference only numeric evidence IDs supplied in the prompt. Unknown IDs are
    discarded, so generated prose cannot create a new source of truth.
    """
    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        return []

    catalog = _catalog(events, context_pack)
    if not catalog:
        return []
    selected_model = model or os.getenv("FORGE_INCIDENT_MODEL", "gpt-5-mini")
    evidence_text = "\n".join(
        f"[{index}] {item.source_type} | {item.source} | {item.detail}"
        for index, item in enumerate(catalog)
    )
    prompt = (
        "Analyze this incident evidence. Produce at most 4 root-cause hypotheses. "
        "Every hypothesis must cite evidence_ids from the numbered catalog. Distinguish correlation "
        "from causation, include concrete falsifiers, and lower confidence when causal evidence is weak.\n\n"
        + evidence_text
    )
    body = {
        "model": selected_model,
        "input": [
            {"role": "system", "content": "You are a cautious production incident diagnostician."},
            {"role": "user", "content": prompt},
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "incident_analysis",
                "strict": True,
                "schema": _schema(),
            }
        },
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
        parsed = AdvisorOutput.model_validate_json(_output_text(payload))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, json.JSONDecodeError):
        return []

    results: list[RootCauseHypothesis] = []
    for item in parsed.hypotheses:
        refs = [catalog[index] for index in item.evidence_ids if 0 <= index < len(catalog)]
        if not refs:
            continue
        results.append(
            RootCauseHypothesis(
                title=item.title,
                explanation=item.explanation,
                confidence=item.confidence,
                affected_services=item.affected_services,
                evidence=refs,
                falsifiers=item.falsifiers,
            )
        )
    return results
