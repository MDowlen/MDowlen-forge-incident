# ForgeIncident

**Evidence-grounded multi-agent incident triage and root-cause analysis.**

ForgeIncident turns operational signals into a structured incident report by correlating logs, metrics, traces, alerts, and deployments with repository code, runbooks, architecture decisions, and prior operational documentation retrieved through ForgeContext.

## Core rule

> Correlation creates a hypothesis. Evidence earns confidence. Human operators approve risky remediation.

## Architecture

```text
Logs / Metrics / Traces / Alerts / Deployments
                  |
                  v
           Normalize Agent
                  |
                  v
          Correlation Agent
                  |
                  +-----------------------------+
                  |                             |
                  v                             v
        Correlated timeline             ForgeContext
                                        code/runbooks/
                                      ADRs/postmortems
                  |                             |
                  +-------------+---------------+
                                v
                         Diagnosis Agent
                                |
                   evidence + confidence
                   + explicit falsifiers
                                |
                                v
                       Remediation Agent
                                |
                   human approval boundaries
                                |
                                v
                          Report Agent
```

## What it does

- normalizes timestamped operational signals
- groups related service signals into deterministic time windows
- detects deployment/failure and metric/error correlations
- retrieves grounded repository and operational context with ForgeContext
- produces ranked root-cause hypotheses with evidence and falsifiers
- proposes remediation with verification steps and human-approval boundaries
- evaluates RCA quality using hypothesis hit rate, affected-service recall, and evidence coverage
- runs as a local CLI and in CI across Python 3.11-3.13

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e '.[dev]'

forge-incident analyze fixtures/deployment_regression.json
forge-incident analyze fixtures/deployment_regression.json --json
forge-incident eval run evals/example.json
```

## Signal schema

Each signal contains:

- `kind`: log, metric, trace, deployment, or alert
- `timestamp`
- `service`
- `message`
- optional numeric `value` and `unit`
- labels/source metadata

## Root-cause contract

A hypothesis is not just prose. It contains:

- title and explanation
- confidence score
- affected services
- concrete evidence references
- explicit falsifiers that could disprove it

That distinction is important: ForgeIncident can identify a deployment that occurred immediately before an outage, but it labels that as correlation until rollback, comparison, or other causal evidence confirms it.

## Safety model

ForgeIncident does **not** automatically execute destructive remediation. Rollback, traffic-shift, capacity, or other production-changing actions are returned with `requires_human_approval=true`. The system can automate analysis while keeping operational authority with deterministic controls and human operators.

## Evaluation

`forge-incident eval run` reports:

- **Hypothesis hit rate** — whether the expected causal concept appeared in the generated hypotheses
- **Affected-service recall** — whether known affected services were identified
- **Evidence coverage** — fraction of hypotheses containing explicit evidence

## Ecosystem

```text
ForgeContext -> grounded repository intelligence
     |
     +--> ForgePR -> pull-request review + CI gates
     |
     +--> ForgeIncident -> operational triage + RCA
```

## Development

```bash
ruff check src tests
pytest -q
```

## Roadmap

- model-backed diagnostic and remediation agents with structured outputs
- trace-span causal ordering and cross-service dependency graphs
- Prometheus/OpenTelemetry/log-platform adapters
- incident timeline visualization/API layer
- postmortem feedback loop and regression evaluation
- Slack/PagerDuty-style notification integrations

## License

MIT © 2026 Mareza Dowlen
