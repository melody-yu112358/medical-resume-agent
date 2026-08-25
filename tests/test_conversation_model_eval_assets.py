import json
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_conversation_model_eval_cases_are_synthetic_and_cover_required_risks():
    payload = json.loads((ROOT / "data" / "evaluations" / "conversation_model_eval_cases.json").read_text(encoding="utf-8"))
    cases = payload["cases"]
    tags = {tag for case in cases for tag in case["tags"]}

    assert len(cases) >= 20
    assert len({case["id"] for case in cases}) == len(cases)
    assert {"ambiguous_experience", "mixed_responsibility", "supervised_to_independent", "self_correction", "professional_rewrite", "explicit_exaggeration", "insufficient_information", "multiple_action_method_tool", "semantic_warning"}.issubset(tags)
    assert "synthetic" in payload["privacy"].lower()


def test_model_eval_documentation_keeps_network_runs_opt_in():
    documentation = (ROOT / "docs" / "conversation_model_eval.md").read_text(encoding="utf-8")

    assert "pytest -q" in documentation
    assert "LLM_BASE_URL" in documentation
    assert "SKIPPED" in documentation
    assert "Fact fidelity" in documentation
