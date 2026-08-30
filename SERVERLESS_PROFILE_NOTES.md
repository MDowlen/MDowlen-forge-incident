# ForgeIncident serverless profile

v0.3.1 separates the lightweight incident workflow from the optional ForgeContext repository-grounding dependency.

Default install keeps correlation, deterministic RCA, optional model advising, falsifiers, remediation planning, and typed reports small enough for serverless environments.

Install the `context` extra when repository/runbook/postmortem grounding is required:

```bash
pip install 'forge-incident[context]'
```

The full CI development profile continues to install and test the context extra so the richer mode remains covered while lightweight consumers avoid pulling the large vector/parsing stack into every runtime.
