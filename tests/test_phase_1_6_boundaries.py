import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]
SKILL = ROOT / "skill-lite" / "medical-resume-skill"


def test_phase_1_6_rules_and_boundary_cases_are_machine_readable(tmp_path):
    rules = json.loads((SKILL / "references" / "generalist-beta-negative-mapping-rules.json").read_text(encoding="utf-8"))
    by_id = {rule["id"]: rule for rule in rules["rules"]}
    assert "project_coordination_requires_project_ownership_evidence" in by_id
    assert "internal_presentation_requires_external_communication_evidence" in by_id

    package_root = tmp_path / "medical-resume-skill"
    shutil.copytree(SKILL, package_root)
    result = subprocess.run(
        [
            sys.executable,
            str(package_root / "scripts" / "validate_generalist_beta.py"),
            "--boundary-cases",
            str(package_root / "references" / "phase-1-6-boundary-cases.json"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "plus boundary cases" in result.stdout


def test_phase_1_6_learning_loop_has_cross_jd_evidence_and_graduation_gates():
    learning = json.loads((SKILL / "references" / "phase-1-6-learning-loop.json").read_text(encoding="utf-8"))
    assert len(learning["jd_sets"]["clinical_operations"]) == 5
    assert len(learning["jd_sets"]["heor_rwe_evidence_oriented"]) == 5
    assert len(learning["fixed_personas"]) == 5
    for direction in learning["stress_results"].values():
        assert direction["stable_core"]
        assert direction["unstable_or_jd_specific"]
        assert direction["candidate_positive_mappings"]
        assert direction["candidate_forbidden_claims"]
        assert "do not graduate" in direction["maturity"] or "no evidence yet" in direction["maturity"]
    criteria = learning["graduation_criteria"]
    for required in ("minimum_real_jd_coverage", "persona_coverage", "stable_rules", "conformance", "usefulness", "unsupported_claim_rate", "jd_dependence"):
        assert required in criteria
