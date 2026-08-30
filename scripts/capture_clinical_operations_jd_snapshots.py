"""Capture reproducible public Clinical Operations JD snapshots.

This is a research-only collector.  It never sends personal data and does not
create, modify, or route a Role Pack.  The public Ashby board response is the
source; each saved job object retains its original URL and a canonical SHA-256
digest so a reviewer can distinguish a current retrieval from a historical
record.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).parents[1]
OUTPUT = ROOT / "skill-lite" / "medical-resume-skill" / "references" / "clinical-operations-jd-snapshots"

SOURCES = (
    {"record_id": "co-current-01", "provider": "ashby", "source_key": "generatorhealth", "job_id": "f658142b-7f24-44db-bbda-7125a969667d", "responsibility_band": "specialist"},
    {"record_id": "co-current-02", "provider": "ashby", "source_key": "capable", "job_id": "9cfe1c48-0278-46ae-b0e5-a41b09d171b6", "responsibility_band": "individual_contributor_to_lead"},
    {"record_id": "co-current-03", "provider": "ashby", "source_key": "sprinter-health", "job_id": "47a672f8-a7b1-4f2a-8639-7919245bf787", "responsibility_band": "senior_individual_contributor"},
    {"record_id": "co-current-04", "provider": "ashby", "source_key": "brooklyn-health", "job_id": "847e154c-d814-477f-8512-97e86daacb21", "responsibility_band": "manager"},
    {"record_id": "co-current-05", "provider": "ashby", "source_key": "pharmacy1sthealth", "job_id": "7b576c08-8b51-45dd-82ce-6a687db01a45", "responsibility_band": "associate"},
    {"record_id": "co-current-06", "provider": "ashby", "source_key": "iota-bio", "job_id": "e5b49217-d216-4923-8d93-7556b2e877fb", "responsibility_band": "manager"},
    {"record_id": "co-current-07", "provider": "lever", "source_key": "NuvoAir", "job_id": "4939bba8-2b84-46c9-bc44-7e45e3f32e3b", "responsibility_band": "intern"},
    {"record_id": "co-current-08", "provider": "lever", "source_key": "dozee", "job_id": "d844640a-e004-4dd2-a410-d3fcd5cb08ba", "responsibility_band": "clinical_operations_leadership"},
)


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def fetch_json(url: str) -> object:
    request = Request(url, headers={"User-Agent": "medical-resume-agent-validation/1.0"})
    with urlopen(request, timeout=30) as response:  # nosec B310 - fixed public HTTPS endpoint
        return json.loads(response.read().decode("utf-8"))


def fetch_job(source: dict) -> tuple[object, dict, str, str]:
    if source["provider"] == "ashby":
        response_url = f"https://api.ashbyhq.com/posting-api/job-board/{source['source_key']}"
        response_data = fetch_json(response_url)
        job = next((item for item in response_data["jobs"] if item["id"] == source["job_id"]), None)
        job_url = job["jobUrl"] if job else ""
    elif source["provider"] == "lever":
        response_url = f"https://api.lever.co/v0/postings/{source['source_key']}?mode=json"
        response_data = fetch_json(response_url)
        job = next((item for item in response_data if item["id"] == source["job_id"]), None)
        job_url = job["hostedUrl"] if job else ""
    else:
        raise ValueError(f"unsupported provider: {source['provider']}")
    if job is None:
        raise RuntimeError(f"{source['record_id']}: posting {source['job_id']} is no longer publicly present")
    return response_data, job, response_url, job_url


def main() -> None:
    staging = OUTPUT.with_name(f"{OUTPUT.name}.staging")
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    captured_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    index_entries = []
    for source in SOURCES:
        response_data, job, response_url, job_url = fetch_job(source)

        job_digest = hashlib.sha256(canonical_bytes(job)).hexdigest()
        response_digest = hashlib.sha256(canonical_bytes(response_data)).hexdigest()
        snapshot = {
            "schema_version": "clinical-operations-jd-snapshot-v1",
            "record_id": source["record_id"],
            "captured_at": captured_at,
            "retrieval_status": "current_retrieved",
            "source": {
                "provider": f"{source['provider']} public job-posting API",
                "response_url": response_url,
                "job_url": job_url,
                "job_id": source["job_id"],
                "response_sha256": response_digest,
                "job_snapshot_sha256": job_digest,
                "digest_canonicalization": "UTF-8 JSON; keys sorted; compact separators; SHA-256",
            },
            "job": job,
        }
        filename = f"{source['record_id']}.json"
        (staging / filename).write_bytes(canonical_bytes(snapshot) + b"\n")
        index_entries.append(
            {
                "record_id": source["record_id"],
                "file": filename,
                "company_board": source["source_key"],
                "title": job.get("title") or job["text"],
                "responsibility_band": source["responsibility_band"],
                "job_url": job_url,
                "captured_at": captured_at,
                "retrieval_status": "current_retrieved",
                "job_snapshot_sha256": job_digest,
            }
        )

    index = {
        "schema_version": "clinical-operations-jd-snapshot-index-v1",
        "scope": "Current public JD corpus for Clinical Operations graduation validation; not a Role Pack.",
        "captured_at": captured_at,
        "entries": index_entries,
        "historical_corpus_note": "The 2026-08-30 historical URLs remain provenance leads only until a saved full snapshot and digest are available. They are not counted by this index.",
    }
    (staging / "index.json").write_bytes(canonical_bytes(index) + b"\n")
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    staging.rename(OUTPUT)


if __name__ == "__main__":
    main()
