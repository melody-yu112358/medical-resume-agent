from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
EVIDENCE_PATH = ROOT / "docs" / "research" / "role-validation" / "cdm" / "candidate-evidence-v1.json"


def test_cdm_conformance_preparation_requires_identifiable_model_provenance():
    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    preparation = evidence["conformance_preparation"]

    assert preparation["status"] == "blocked_pending_identifiable_model"
    assert preparation["fixed_case_ids"] == ["cdm-positive", "cdm-partial", "cdm-negative"]
    assert {"factuality", "ownership", "usefulness", "unsupported_claim_audit"} <= set(preparation["rubric"])
    assert evidence["conformance_ledger"]["runs"] == []
