"""Validate the evidence needed to promote Clinical Operations from Candidate.

This validator intentionally reports ``pending`` until complete, auditable run
records meet every Candidate-to-Validated threshold.  It does not create a
Role Pack or infer missing model evidence.
"""

from __future__ import annotations

import hashlib
import json
import statistics
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]
SNAPSHOTS = ROOT / "skill-lite" / "medical-resume-skill" / "references" / "clinical-operations-jd-snapshots"
LEDGER = ROOT / "skill-lite" / "medical-resume-skill" / "references" / "clinical-operations-conformance-ledger.json"


def canonical_digest(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    index = json.loads((SNAPSHOTS / "index.json").read_text(encoding="utf-8"))
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    entries = index["entries"]
    require(len(entries) >= 8, "Clinical Operations needs at least eight current or archived full JD snapshots")
    require(len({entry["company_board"] for entry in entries}) >= 5, "JD corpus needs at least five employers")
    require(len({entry["responsibility_band"] for entry in entries}) >= 3, "JD corpus needs at least three responsibility bands")

    snapshot_digests = set()
    for entry in entries:
        snapshot = json.loads((SNAPSHOTS / entry["file"]).read_text(encoding="utf-8"))
        require(snapshot["retrieval_status"] in {"current_retrieved", "historical_archived"}, f"invalid retrieval status: {entry['record_id']}")
        require(snapshot["source"]["job_url"] == entry["job_url"], f"URL mismatch: {entry['record_id']}")
        digest = canonical_digest(snapshot["job"])
        require(digest == snapshot["source"]["job_snapshot_sha256"], f"job digest mismatch: {entry['record_id']}")
        require(digest == entry["job_snapshot_sha256"], f"index digest mismatch: {entry['record_id']}")
        require(bool(snapshot["job"].get("descriptionPlain")), f"missing complete description: {entry['record_id']}")
        snapshot_digests.add(digest)

    required = set(ledger["requirements"]["required_fields_per_run"])
    complete_runs = []
    for run in ledger["runs"]:
        require(required <= set(run), f"incomplete run record: {run.get('run_id', '<missing>')}")
        require(run["jd_snapshot_sha256"] in snapshot_digests, f"unknown JD digest: {run['run_id']}")
        complete_runs.append(run)

    scores = [run["scores"] for run in complete_runs]
    audits = [run["unsupported_claim_audit"] for run in complete_runs]
    model_ids = {run["model_id"] for run in complete_runs}
    factuality = statistics.fmean(score["factuality"] for score in scores) if scores else 0.0
    ownership = statistics.fmean(score["ownership"] for score in scores) if scores else 0.0
    usefulness = statistics.median(score["usefulness"] for score in scores) if scores else 0.0
    critical = sum(audit["critical_count"] for audit in audits)
    noncritical = sum(audit["noncritical_count"] for audit in audits)
    audited_claims = sum(audit["audited_claim_count"] for audit in audits)
    noncritical_rate = noncritical / audited_claims if audited_claims else 1.0

    thresholds = ledger["requirements"]
    validated = (
        len(complete_runs) >= thresholds["minimum_complete_runs"]
        and len(model_ids) >= thresholds["minimum_distinct_model_ids"]
        and factuality >= thresholds["minimum_factuality_average"]
        and ownership >= thresholds["minimum_ownership_average"]
        and usefulness >= thresholds["minimum_usefulness_median"]
        and critical == thresholds["critical_unsupported_claims"]
        and noncritical_rate < thresholds["maximum_noncritical_unsupported_claim_rate"]
    )
    print(json.dumps({
        "status": "validated_candidate" if validated else "pending_cross_model_conformance",
        "jd_snapshot_count": len(entries),
        "company_count": len({entry["company_board"] for entry in entries}),
        "complete_run_count": len(complete_runs),
        "distinct_model_ids": len(model_ids),
        "factuality_average": factuality,
        "ownership_average": ownership,
        "usefulness_median": usefulness,
        "critical_unsupported_claims": critical,
        "noncritical_unsupported_claim_rate": noncritical_rate,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
