from __future__ import annotations

from .models import IncidentReport


def render_markdown(report: IncidentReport) -> str:
    lines = [
        f"# {report.incident_id}: {report.title}",
        "",
        f"**Severity:** {report.severity.value}",
        f"**Status:** {report.status.value}",
        f"**Started:** {report.started_at.isoformat()}",
        f"**Generated:** {report.generated_at.isoformat()}",
        "",
        "## Summary",
        "",
        report.summary,
        "",
        "## Affected services",
        "",
    ]
    lines.extend(f"- {service}" for service in report.affected_services)
    lines.extend(["", "## Timeline", ""])
    for event in report.correlated_events:
        lines.append(
            f"- **{event.start_time.isoformat()} - {event.end_time.isoformat()}** "
            f"`{event.service}` ({event.severity.value}): {event.summary}"
        )

    lines.extend(["", "## Root-cause hypotheses", ""])
    for index, item in enumerate(report.hypotheses, start=1):
        lines.extend(
            [
                f"### {index}. {item.title} ({item.confidence:.0%})",
                "",
                item.explanation,
                "",
                "**Evidence**",
            ]
        )
        lines.extend(
            f"- [{evidence.source_type}] `{evidence.source}` - {evidence.detail}"
            for evidence in item.evidence
        )
        lines.append("")
        lines.append("**Falsifiers**")
        lines.extend(f"- {falsifier}" for falsifier in item.falsifiers)
        lines.append("")

    lines.extend(["## Mitigation / remediation plan", ""])
    for step in report.remediation:
        approval = "human approval required" if step.requires_human_approval else "no approval required"
        lines.extend(
            [
                f"- **{step.action}** ({approval})",
                f"  - Why: {step.rationale}",
                f"  - Verify: {step.verification}",
            ]
        )
    lines.extend(
        [
            "",
            "## Follow-up checklist",
            "",
            "- [ ] Confirm or reject the leading hypothesis with causal evidence.",
            "- [ ] Record the mitigation outcome and verification metrics.",
            "- [ ] Add prevention work with owners and due dates.",
            "- [ ] Store this postmortem where ForgeContext can index it for future incidents.",
            "",
        ]
    )
    return "\n".join(lines)
