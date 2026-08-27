from forge_incident.models import EvidenceRef, RootCauseHypothesis
from forge_incident.remediation import plan_remediation


def test_deployment_remediation_requires_human_approval():
    hypothesis = RootCauseHypothesis(
        title="Recent deployment correlated with failure onset",
        explanation="deployment then failures",
        confidence=0.8,
        evidence=[EvidenceRef(source_type="deployment", source="deploy", detail="v42", score=1.0)],
    )
    steps = plan_remediation([hypothesis])
    rollback = next(step for step in steps if "rollback" in step.action.lower())
    assert rollback.requires_human_approval is True
    assert rollback.verification
