from __future__ import annotations

import json
from pathlib import Path

from jsonschema import validate

from scripts.career_track_orchestrator import OUTPUT_PATH, build_state, decide_next_action, import_candidate_evidence


ROOT = Path(__file__).parents[1]


def test_current_candidate_evidence_dry_run_routes_all_tracks_to_researcher():
    state = build_state()

    assert {track["career_id"] for track in state["tracks"]} == {
        "clinical_research_associate",
        "clinical_data_management",
        "medical_device_clinical_application_specialist",
        "pharmacovigilance_drug_safety",
    }
    for track in state["tracks"]:
        assert track["current_tier"] == "beta"
        assert track["stage"] == "research"
        assert track["next_action"] == "collect_more_jds"
        assert track["assigned_agent"] == "researcher"
        assert track["human_required"] is False
        assert track["graduation_status"] == "not_eligible"


def test_generated_snapshot_matches_evidence_and_schema():
    expected = build_state()
    actual = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "schemas" / "career-track-state.schema.json").read_text(encoding="utf-8"))

    assert actual == expected
    validate(instance=actual, schema=schema)


def test_only_eligible_state_requires_human_canonicalization_approval():
    eligible = decide_next_action({
        "career_id": "synthetic_eligible", "current_tier": "candidate", "stage": "release_gate",
        "jd_count": 8, "qualifying_jd_count": 8, "company_count": 5, "persona_count": 8,
        "mapping_status": "complete", "negative_mapping_status": "complete", "review_status": "passed",
        "conformance_status": "passed", "graduation_status": "not_eligible", "blockers": [],
        "next_action": "", "assigned_agent": "release_gate", "human_required": False,
        "execution_status": "review_pending", "remote_sync_status": "synced",
    })

    assert eligible["graduation_status"] == "eligible_for_canonicalization"
    assert eligible["next_action"] == "request_canonicalization_approval"
    assert eligible["assigned_agent"] == "human"
    assert eligible["human_required"] is True


def test_remote_sync_delay_does_not_reopen_or_duplicate_work():
    delayed = decide_next_action({
        "career_id": "synthetic_delay", "current_tier": "beta", "stage": "research",
        "jd_count": 0, "qualifying_jd_count": 0, "company_count": 0, "persona_count": 0,
        "mapping_status": "incomplete", "negative_mapping_status": "incomplete", "review_status": "not_requested",
        "conformance_status": "not_started", "graduation_status": "not_eligible", "blockers": [],
        "next_action": "", "assigned_agent": "researcher", "human_required": False,
        "execution_status": "awaiting_remote_sync", "remote_sync_status": "awaiting_remote_sync",
    })

    assert delayed["next_action"] == "resume_remote_sync"
    assert delayed["assigned_agent"] == "researcher"
    assert delayed["human_required"] is False


def test_non_countable_snapshots_cannot_satisfy_jd_or_company_graduation_coverage():
    evidence = {
        "career_id": "synthetic_coverage", "fixed_personas": list(range(8)),
        "mappings": {key: [key] for key in ("direct", "transferable", "partial", "gap")},
        "negative_mappings": ["boundary"], "conformance_ledger": {},
        "jd_snapshots": [
            {"employer": f"countable-{index}", "status": "current_public_full"}
            for index in range(5)
        ] + [
            {"employer": f"search-only-{index}", "status": "search_extract_not_countable"}
            for index in range(3)
        ],
    }

    decided = decide_next_action(import_candidate_evidence(evidence))

    assert decided["jd_count"] == 8
    assert decided["qualifying_jd_count"] == 5
    assert decided["company_count"] == 5
    assert decided["next_action"] == "collect_more_jds"
    assert "insufficient_jd_coverage" in decided["blockers"]


def test_non_countable_employers_do_not_satisfy_company_graduation_coverage():
    evidence = {
        "career_id": "synthetic_company_coverage", "fixed_personas": list(range(8)),
        "mappings": {key: [key] for key in ("direct", "transferable", "partial", "gap")},
        "negative_mappings": ["boundary"], "conformance_ledger": {},
        "jd_snapshots": [
            {"employer": "countable-company", "status": "current_public_full"}
            for _ in range(8)
        ] + [
            {"employer": f"search-only-{index}", "status": "search_extract_not_countable"}
            for index in range(4)
        ],
    }

    decided = decide_next_action(import_candidate_evidence(evidence))

    assert decided["jd_count"] == 12
    assert decided["qualifying_jd_count"] == 8
    assert decided["company_count"] == 1
    assert decided["next_action"] == "collect_more_jds"
    assert "insufficient_company_coverage" in decided["blockers"]
