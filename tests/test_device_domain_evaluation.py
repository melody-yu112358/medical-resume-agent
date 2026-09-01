import json
from pathlib import Path


def test_device_domain_evaluation_is_evidence_bound_and_useful():
    cases = json.loads((Path(__file__).parents[1] / "docs/research/role-validation/device-clinical-application/domain-evaluation-v1.json").read_text(encoding="utf-8"))["cases"]
    assert {case["expected_mapping_class"] for case in cases} == {"direct", "transferable", "partial", "gap"}
    assert len({case["jd_id"] for case in cases}) >= 4
    assert all(case["factuality"] == case["ownership"] == "PASS" and case["critical_unsupported_claims"] == 0 for case in cases)
    assert sorted(case["usefulness"] for case in cases)[1] >= 4
