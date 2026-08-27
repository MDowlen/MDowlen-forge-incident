from __future__ import annotations

from .models import RemediationStep, RootCauseHypothesis, Severity


def plan_remediation(hypotheses: list[RootCauseHypothesis]) -> list[RemediationStep]:
    steps: list[RemediationStep] = []
    if not hypotheses:
        return [
            RemediationStep(
                action="Collect additional logs, metrics, traces, and deployment history",
                rationale="There is not enough evidence to recommend a targeted mitigation.",
                risk=Severity.info,
                verification="Confirm at least one reproducible failure signal and a time-correlated lead.",
                requires_human_approval=False,
            )
        ]

    top = hypotheses[0]
    if "deployment" in top.title.lower():
        steps.append(
            RemediationStep(
                action="Prepare rollback or traffic shift to the last known-good release",
                rationale="The leading hypothesis correlates failure onset with a recent deployment.",
                risk=Severity.high,
                verification="Compare error rate, latency, and availability before and after rollback/shift.",
                requires_human_approval=True,
            )
        )
    if "saturation" in top.title.lower() or "latency" in top.title.lower():
        steps.append(
            RemediationStep(
                action="Reduce load or increase safe capacity while investigating the bottleneck",
                rationale="The leading evidence combines degraded metrics with application failures.",
                risk=Severity.warning,
                verification="Verify saturation and error-rate metrics return toward baseline.",
                requires_human_approval=True,
            )
        )

    steps.extend(
        [
            RemediationStep(
                action="Validate the leading hypothesis against its falsifiers",
                rationale="Correlation must not be promoted to root cause without contradictory checks.",
                risk=Severity.info,
                verification="Document which falsifiers were tested and the observed result.",
                requires_human_approval=False,
            ),
            RemediationStep(
                action="Capture the final timeline, causal evidence, mitigation, and prevention work",
                rationale="A reusable postmortem improves future incident retrieval and evaluation.",
                risk=Severity.info,
                verification="Postmortem contains timestamps, evidence links, owner, and follow-up actions.",
                requires_human_approval=False,
            ),
        ]
    )
    return steps
