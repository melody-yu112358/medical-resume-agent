import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
REPORT = ROOT / "skill-lite" / "medical-resume-skill" / "references" / "phase-2-role-validation-evidence.json"


def test_phase_2_clusters_meet_beta_candidate_coverage_structure():
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    for cluster in report["clusters"].values():
        assert len(cluster["jds"]) >= 8
        assert len({jd["company"] for jd in cluster["jds"]}) >= 5
        assert len({jd["level"] for jd in cluster["jds"]}) >= 3
        assert all(jd["url"].startswith("https://") and jd["snapshot"] for jd in cluster["jds"])
        assert len(cluster["personas"]) >= 8
        assert sum(persona["kind"] in {"partial", "negative"} for persona in cluster["personas"]) >= 3
        jd_ids = {jd["id"] for jd in cluster["jds"]}
        for persona in cluster["personas"]:
            assert len(persona["evaluated_jds"]) >= 3
            assert set(persona["evaluated_jds"]) <= jd_ids
        assert cluster["negative_mappings"]


def test_phase_2_standalone_conformance_is_safe_but_not_validated_claim():
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    runs = report["standalone_model_conformance"]["runs"]
    assert len(runs) == 12
    assert all(run["factuality"] >= 4.5 and run["ownership"] >= 4.5 for run in runs)
    assert all(run["unsupported_claims"] == 0 for run in runs)
    assert sorted(run["usefulness"] for run in runs)[len(runs) // 2 - 1] >= 4
    assert "30 runs across two model versions" in " ".join(report["standalone_model_conformance"]["limitations"])


def test_phase_2_keeps_critical_non_claims_explicit():
    report = REPORT.read_text(encoding="utf-8").lower()
    for phrase in ("kpi ownership", "payer engagement", "reimbursement", "client", "project/program ownership"):
        assert phrase in report
