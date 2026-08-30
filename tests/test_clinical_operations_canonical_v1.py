import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
PACK_PATH = ROOT / "data" / "role-packs" / "clinical_operations_v1.json"
REVIEW_PATH = ROOT / "skill-lite" / "medical-resume-skill" / "references" / "clinical-operations-domain-review-v1.json"
SNAPSHOT_PATH = ROOT / "skill-lite" / "medical-resume-skill" / "references" / "clinical-operations-jd-snapshots" / "index.json"


def test_clinical_operations_pack_is_narrow_and_has_all_case_types():
    pack = json.loads(PACK_PATH.read_text(encoding="utf-8"))
    case_types = {case["input"]["case_type"] for case in pack["evaluation_cases"]}
    forbidden = set(pack["forbidden_claims"])

    assert pack["role_pack"] == "clinical_operations_v1"
    assert case_types == {"positive", "partial", "negative"}
    assert len(pack["evaluation_cases"]) == 8
    assert {
        "项目或项目群所有权", "流程或运营所有者", "KPI 所有者", "团队管理",
        "供应商、预算或合同管理", "患者或提供者所有权", "对外、客户或高管沟通",
    } <= forbidden
    assert "healthcare/business operations" in pack["skill_reference"]["boundary_note"]
    assert "management" not in pack["preferred_actions"]


def test_domain_review_is_traceable_and_meets_domain_thresholds():
    review = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    snapshots = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    scores = sorted(case["usefulness_resume_quality"] for case in review["cases"])
    case_types = {
        json.loads(PACK_PATH.read_text(encoding="utf-8"))["evaluation_cases"][index]["input"]["case_type"]
        for index in range(len(review["cases"]))
    }

    assert review["source_provenance"]["current_public_jds"] == len(snapshots["entries"]) == 8
    assert review["source_provenance"]["employers"] >= 5
    assert review["source_provenance"]["responsibility_bands"] >= 3
    assert scores[len(scores) // 2 - 1] >= 4
    assert sum(case["critical_unsupported_claims"] for case in review["cases"]) == 0
    assert case_types == {"positive", "partial", "negative"}
    assert review["result"]["domain_validation"] == "pass_pending_traceable_human_pr_approval"
    assert review["result"]["cross_model_validation"].startswith("pending")
