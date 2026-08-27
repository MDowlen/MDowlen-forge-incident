from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .evaluation import evaluate, load_cases
from .runner import run_fixture

app = typer.Typer(help="ForgeIncident evidence-grounded incident triage CLI")
eval_app = typer.Typer(help="Incident evaluation commands")
app.add_typer(eval_app, name="eval")
console = Console()


@app.command("analyze")
def analyze(
    incident_file: Path = typer.Argument(..., exists=True, dir_okay=False),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Analyze an incident fixture and produce evidence-backed RCA hypotheses."""
    report = run_fixture(incident_file)
    if json_output:
        console.print_json(json.dumps(report.model_dump(mode="json")))
        return

    console.print(f"[bold]{report.incident_id} · {report.severity.value}[/bold]")
    console.print(report.summary)
    console.print(f"Affected services: {', '.join(report.affected_services) or 'unknown'}")

    table = Table(title="Root-cause hypotheses")
    table.add_column("Confidence", justify="right")
    table.add_column("Hypothesis")
    table.add_column("Evidence")
    for item in report.hypotheses:
        table.add_row(f"{item.confidence:.0%}", item.title, str(len(item.evidence)))
    console.print(table)

    actions = Table(title="Remediation plan")
    actions.add_column("Approval")
    actions.add_column("Action")
    actions.add_column("Verification")
    for step in report.remediation:
        actions.add_row("human" if step.requires_human_approval else "not required", step.action, step.verification)
    console.print(actions)


@eval_app.command("run")
def eval_run(dataset: Path = typer.Argument(..., exists=True, dir_okay=False)) -> None:
    """Measure hypothesis hit rate, affected-service recall, and evidence coverage."""
    report = evaluate(load_cases(dataset))
    console.print(f"Cases: [bold]{report.cases}[/bold]")
    console.print(f"Hypothesis hit rate: [bold]{report.hypothesis_hit_rate:.3f}[/bold]")
    console.print(f"Service recall: [bold]{report.mean_service_recall:.3f}[/bold]")
    console.print(f"Evidence coverage: [bold]{report.mean_evidence_coverage:.3f}[/bold]")


if __name__ == "__main__":
    app()
