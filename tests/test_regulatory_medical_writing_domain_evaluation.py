from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
EVALUATION_PATH = (
    ROOT
    / "docs"
    / "research"
    / "role-validation"
    / "regulatory-medical-writing"
    / "domain-evaluation-v1.json"
)


def test_regulatory_medical_writing_domain_evaluation_is_evidence_bound_and_useful():
    cases = json.loads(EVALUATION_PATH.read_text(encoding="utf-8"))["cases"]

    assert {case["expected_mapping_class"] for case in cases} == {
        "direct",
        "transferable",
        "partial",
        "gap",
    }
    assert len({case["jd_id"] for case in cases}) >= 4
    assert all(case["evidence_ids"] and case["allowed_claims"] for case in cases)
    assert all(case["prohibited_claims"] and case["golden_output"] for case in cases)
    assert all(
        case["factuality"] == case["ownership"] == "PASS"
        and case["critical_unsupported_claims"] == 0
        and case["unsupported_claims"] == []
        for case in cases
    )
    assert sorted(case["usefulness"] for case in cases)[len(cases) // 2 - 1] >= 4
