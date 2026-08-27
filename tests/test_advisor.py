from forge_incident.advisor import model_hypotheses


def test_model_advisor_is_optional_without_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert model_hypotheses([], None) == []
