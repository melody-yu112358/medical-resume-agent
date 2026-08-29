import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]
SKILL = ROOT / "skill-lite" / "medical-resume-skill"


def test_generalist_beta_assets_keep_matching_and_claim_safety_separate():
    contract = json.loads((SKILL / "references" / "generalist-beta-contract.json").read_text(encoding="utf-8"))
    assert contract["mapping"]["statuses"] == [
        "direct_evidence", "transferable_evidence", "partial_match", "explicit_gap"
    ]
    assert "unsupported_claim" not in contract["mapping"]["statuses"]
    assert "claim_safety" in contract


def test_generalist_beta_portable_validator_and_negative_case(tmp_path):
    package_root = tmp_path / "medical-resume-skill"
    shutil.copytree(SKILL, package_root)
    validator = package_root / "scripts" / "validate_generalist_beta.py"
    passed = subprocess.run([sys.executable, str(validator)], capture_output=True, text=True, check=False)
    assert passed.returncode == 0, passed.stdout + passed.stderr
    assert "passed: 15 cases" in passed.stdout

    cases_path = package_root / "references" / "generalist-beta-eval-cases.json"
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    cases["cases"][0]["claim_safety"]["candidate_text"] = "主导用户需求洞察并撰写PRD。"
    mutated = tmp_path / "mutated-generalist-cases.json"
    mutated.write_text(json.dumps(cases, ensure_ascii=False), encoding="utf-8")
    failed = subprocess.run(
        [sys.executable, str(validator), "--cases", str(mutated)],
        capture_output=True, text=True, check=False
    )
    assert failed.returncode == 1
    assert "contains prohibited claim" in failed.stdout


def test_product_guidance_does_not_equate_research_problems_with_user_research():
    text = (SKILL / "references" / "generalist-transition-beta.md").read_text(encoding="utf-8")
    assert "not automatically a user need" in text
    assert "must not claim user research" in text


def test_model_conformance_cases_cover_all_fifteen_beta_fixtures():
    eval_cases = json.loads((SKILL / "references" / "generalist-beta-eval-cases.json").read_text(encoding="utf-8"))
    conformance = json.loads((SKILL / "references" / "generalist-beta-model-conformance-cases.json").read_text(encoding="utf-8"))
    assert {case["case_id"] for case in eval_cases["cases"]} == set(conformance["required_case_ids"])
    assert "unsupported_claim_rate" in conformance["scoring_dimensions"]
