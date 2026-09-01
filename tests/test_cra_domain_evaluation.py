import json
from pathlib import Path


def test_cra_domain_evaluation_is_evidence_bound_and_useful():
    path = Path(__file__).parents[1] / "docs/research/role-validation/cra/domain-evaluation-v1.json"
    cases = json.loads(path.read_text(encoding="utf-8"))["cases"]
    assert {case["expected_mapping_class"] for case in cases} == {"direct", "transferable", "partial", "gap"}
    assert len({case["jd_id"] for case in cases}) >= 4
    assert all(case["factuality"] == case["ownership"] == "PASS" for case in cases)
    assert all(case["critical_unsupported_claims"] == 0 for case in cases)
    assert sorted(case["usefulness"] for case in cases)[1] >= 4
