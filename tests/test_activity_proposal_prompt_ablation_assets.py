import json
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_ablation_cases_cover_required_regressions():
    payload = json.loads((ROOT / "data" / "evaluations" / "activity_proposal_prompt_ablation_cases.json").read_text(encoding="utf-8"))

    assert {item["id"] for item in payload["cases"]} >= {"mixed-002", "professional-005", "exaggeration-007", "tool-014", "clinical-018", "multi-method-019"}
    assert "synthetic" in payload["privacy"].lower()


def test_ablation_script_declares_five_variants_and_three_repetitions():
    script = (ROOT / "scripts" / "run_activity_proposal_prompt_ablation.py").read_text(encoding="utf-8")

    assert '"A_base"' in script and '"E_current"' in script
    assert 'default=3' in script
    assert 'hard_rejections' in script
    assert 'structured_raw' in script
