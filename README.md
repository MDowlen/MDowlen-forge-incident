# ForgeIncident

**Evidence-grounded multi-agent incident triage and root-cause analysis.**

ForgeIncident turns operational signals into a structured incident report by correlating logs, metrics, traces, alerts, and deployments with repository code, runbooks, architecture decisions, and prior operational documentation retrieved through ForgeContext.

## Core rule

> Correlation creates a hypothesis. Evidence earns confidence. Human operators approve risky remediation.

## v0.3 capabilities

- typed Pydantic contracts for signals, events, hypotheses, evidence, remediation, and reports
- timestamp normalization and deterministic service/time-window correlation
- deployment/failure and metric/error correlation heuristics
- ForgeContext repository, runbook, ADR, Git-history, and postmortem retrieval
- LangGraph multi-stage workflow: normalize -> correlate -> context -> diagnose -> remediate -> report
- ranked deterministic RCA hypotheses with explicit evidence and falsifiers
- optional OpenAI diagnostic advisor with structured output
- **evidence-constrained AI citations**: model hypotheses may cite only numeric evidence IDs supplied by the system
- safe fallback when no API key/network is available
- remediation plans with verification steps and explicit human-approval boundaries
- Markdown postmortem generation for the knowledge feedback loop
- RCA evaluation: hypothesis hit rate, affected-service recall, evidence coverage
- sample incidents and labeled evaluation fixtures
- Ruff + pytest CI across Python 3.11, 3.12, and 3.13

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
                                   ADRs/Git/postmortems
                  |                             |
                  +-------------+---------------+
                                v
                         Diagnosis Agent
                     /                    \
       deterministic hypotheses      optional AI advisor
                                     evidence IDs only
                     \                    /
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
                                |
                                +--> JSON report
                                +--> Markdown postmortem
                                +--> evaluation feedback
```

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e '.[dev]'

forge-incident analyze fixtures/deployment_regression.json
forge-incident analyze fixtures/deployment_regression.json --json
forge-incident postmortem fixtures/deployment_regression.json -o postmortem.md
forge-incident eval run evals/example.json
```

The deterministic pipeline works without an AI key. To enable optional model enrichment, set `OPENAI_API_KEY` securely. `FORGE_INCIDENT_MODEL` can override the default model. Secrets are read from the environment and are not written into incident reports or ForgeContext indexes.

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

## AI evidence boundary

The optional model advisor never receives permission to invent file paths, dashboards, or log sources. ForgeIncident first builds an evidence catalog from correlated operational signals and ForgeContext citations. The model receives numbered entries such as `[0]`, `[1]`, and `[2]` and may return only those numeric IDs. Unknown IDs are discarded, and a model hypothesis without valid evidence is rejected.

This keeps the LLM in the role of **reasoning over evidence**, not creating the evidence itself.

## Safety model

ForgeIncident does **not** automatically execute destructive remediation. Rollback, traffic-shift, capacity, or other production-changing actions are returned with `requires_human_approval=true`. The system automates analysis while keeping production authority with human operators and deterministic controls.

## Postmortem feedback loop

```text
incident signals
      -> RCA
      -> mitigation
      -> Markdown postmortem
      -> repository/knowledge base
      -> ForgeContext indexes it
      -> future incidents retrieve prior evidence
```

This turns incident response history into reusable operational memory instead of letting every outage start from zero.

## Evaluation

`forge-incident eval run` reports:

- **Hypothesis hit rate** — whether an expected causal concept appeared in generated hypotheses
- **Affected-service recall** — whether known affected services were identified
- **Evidence coverage** — fraction of hypotheses containing explicit evidence

The labeled fixtures make RCA changes regression-testable rather than judging quality only from demos.

## Ecosystem

```text
ForgeContext -> grounded repository intelligence
     |
     +--> ForgePR -> pull-request review + deterministic CI gates
     |
     +--> ForgeIncident -> incident triage + evidence-backed RCA
```

ForgePR asks, "Could this change break the system?"
ForgeIncident asks, "The system is breaking now — what evidence explains why?"
Both reuse the same grounded context infrastructure.

## Development

```bash
ruff check src tests
pytest -q
```

## Future extensions

- native Prometheus/OpenTelemetry/log-platform adapters
- trace-span causal ordering and cross-service dependency graphs
- incident timeline visualization/API layer
- Slack/PagerDuty-style notification integrations
- historical false-positive and time-to-mitigation dashboards

## License

MIT © 2026 Mareza Dowlen
