import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
REPORT = ROOT / "skill-lite" / "medical-resume-skill" / "references" / "phase-1-5-real-jd-conformance.json"


def test_real_jd_conformance_report_has_five_traceable_runs():
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    source = report["skill_source"]
    # This report is a historical conformance record. Its digest is intentionally
    # not recomputed after later Beta rule changes.
    assert len(source["digest_sha256"]) == 64
    assert source["files"]
    runs = report["runs"]
    assert len(runs) == 5
    assert {run["persona"] for run in runs} == {"A", "B", "C"}
    for run in runs:
        snapshot = run["jd_snapshot"]
        assert snapshot["source_type"] == "url"
        assert snapshot["retrieval_status"] == "retrieved"
        assert snapshot["url"].startswith("https://")
        assert snapshot["source_digest_sha256"] == hashlib.sha256(
            snapshot["source_excerpt"].encode("utf-8")
        ).hexdigest()


def test_real_jd_conformance_preserves_facts_and_reports_gaps():
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    forbidden_by_run = {
        run["run_id"]: set(run["prohibited_claims"])
        for run in report["runs"]
    }
    for run in report["runs"]:
        mappings = run["mapping"]
        assert any(item["status"] == "explicit_gap" for item in mappings)
        assert run["final_audit"]["ownership"] == "pass"
        assert run["final_audit"]["prohibited_claims_detected"] == []
        wording = " ".join(run["resume_wording"])
        assert not any(claim.lower() in wording.lower() for claim in forbidden_by_run[run["run_id"]])
        assert run["scores"]["usefulness_resume_quality"] >= 4
        assert run["scores"]["unsupported_claim_rate"] == 0


def test_product_and_consulting_boundaries_are_exercised():
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    runs = {run["run_id"]: run for run in report["runs"]}
    assert "user research" in runs["product-maple-A"]["prohibited_claims"]
    assert "client delivery" in runs["consulting-beghou-A"]["prohibited_claims"]
    assert "payer engagement" in runs["heor-grail-A"]["prohibited_claims"]
    assert "revenue growth" in runs["commercial-penumbra-C"]["prohibited_claims"]
    assert "KPI ownership" in runs["operations-salma-B"]["prohibited_claims"]
