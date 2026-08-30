import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]
VALIDATOR = ROOT / "scripts" / "validate_clinical_operations_candidate.py"
LEDGER = ROOT / "skill-lite" / "medical-resume-skill" / "references" / "clinical-operations-conformance-ledger.json"


def test_candidate_validator_keeps_cross_model_graduation_pending_without_complete_runs():
    result = subprocess.run([sys.executable, str(VALIDATOR)], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    scorecard = json.loads(result.stdout)
    assert scorecard["status"] == "pending_cross_model_conformance"
    assert scorecard["complete_run_count"] == 0
    assert scorecard["distinct_model_ids"] == 0


def test_ledger_requires_exact_model_and_complete_audit_artifacts():
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    required = set(ledger["requirements"]["required_fields_per_run"])
    assert {"model_id", "prompt", "input", "output", "jd_snapshot_sha256", "skill_source_digest_sha256"} <= required
    assert ledger["model_execution_plan"][0]["exact_deployment_version"] == "unavailable"
    assert ledger["model_execution_plan"][1]["model_id"] == "gpt-5.4-2026-03-05"
