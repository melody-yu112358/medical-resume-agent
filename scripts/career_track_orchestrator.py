"""Deterministic governance-only Career Track State generator.

This module neither invokes agents nor mutates product/runtime state.  It turns
versioned Candidate evidence into a dispatch contract a supported orchestrator
may consume later.
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = ROOT / "docs" / "research" / "role-validation"
OUTPUT_PATH = ROOT / "docs" / "research" / "career-track-states-v1.json"
EVIDENCE_PATHS = {
    "clinical_research_associate": "cra/candidate-evidence-v1.json",
    "clinical_data_management": "cdm/candidate-evidence-v1.json",
    "medical_device_clinical_application_specialist": "device-clinical-application/candidate-evidence-v1.json",
    "pharmacovigilance_drug_safety": "pharmacovigilance/candidate-evidence-v1.json",
}


def _complete_mapping(evidence: dict[str, Any]) -> bool:
    mappings = evidence.get("mappings") or {}
    return all(isinstance(mappings.get(key), list) and mappings[key] for key in ("direct", "transferable", "partial", "gap"))


def _is_qualifying_snapshot(snapshot: dict[str, Any]) -> bool:
    """Exclude explicitly non-countable search snippets from graduation coverage."""
    return snapshot.get("status") != "search_extract_not_countable"


def import_candidate_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    snapshots = evidence.get("jd_snapshots") or []
    qualifying_snapshots = [item for item in snapshots if _is_qualifying_snapshot(item)]
    conformance = evidence.get("conformance_ledger") or {}
    return {
        "career_id": evidence["career_id"],
        "current_tier": "beta",
        "stage": "research",
        "jd_count": len(snapshots),
        "qualifying_jd_count": len(qualifying_snapshots),
        "company_count": len({item.get("employer") for item in qualifying_snapshots if item.get("employer")}),
        "persona_count": len(evidence.get("fixed_personas") or []),
        "mapping_status": "complete" if _complete_mapping(evidence) else "incomplete",
        "negative_mapping_status": "complete" if evidence.get("negative_mappings") else "incomplete",
        "review_status": "not_requested",
        "conformance_status": "passed" if conformance.get("status") == "passed" else "not_started",
        "graduation_status": "not_eligible",
        "blockers": [],
        "next_action": "",
        "assigned_agent": "researcher",
        "human_required": False,
        "execution_status": "completed_local",
        "remote_sync_status": "synced",
        "source_graduation_status": evidence.get("graduation_status"),
    }


def decide_next_action(track: dict[str, Any]) -> dict[str, Any]:
    """Apply the published gate order without advancing a tier automatically."""
    result = dict(track)
    blockers: list[str] = []
    if result.get("execution_status") == "awaiting_remote_sync" or result.get("remote_sync_status") == "awaiting_remote_sync":
        result.update(stage="research", blockers=["remote_sync_delay"], next_action="resume_remote_sync", assigned_agent="researcher", human_required=False)
        return result
    if result["qualifying_jd_count"] < 8 or result["company_count"] < 5:
        if result["qualifying_jd_count"] < 8:
            blockers.append("insufficient_jd_coverage")
        if result["company_count"] < 5:
            blockers.append("insufficient_company_coverage")
        result.update(stage="research", blockers=blockers, next_action="collect_more_jds", assigned_agent="researcher", human_required=False, graduation_status="not_eligible")
        return result
    if result["persona_count"] < 8 or result["mapping_status"] != "complete" or result["negative_mapping_status"] != "complete":
        if result["persona_count"] < 8:
            blockers.append("insufficient_persona_coverage")
        if result["mapping_status"] != "complete":
            blockers.append("incomplete_mappings")
        if result["negative_mapping_status"] != "complete":
            blockers.append("incomplete_negative_mappings")
        result.update(stage="candidate_builder", blockers=blockers, next_action="complete_candidate_assets", assigned_agent="candidate_builder", human_required=False, graduation_status="not_eligible")
        return result
    if result["review_status"] == "changes_requested":
        result.update(stage="candidate_builder", blockers=["review_changes_requested"], next_action="address_review_findings", assigned_agent="implementer", human_required=False, graduation_status="not_eligible")
        return result
    if result["review_status"] != "passed":
        result.update(stage="review", blockers=["independent_review_required"], next_action="request_independent_review", assigned_agent="reviewer", human_required=False, graduation_status="not_eligible")
        return result
    if result["conformance_status"] != "passed":
        result.update(stage="conformance", blockers=["conformance_incomplete"], next_action="run_conformance", assigned_agent="conformance", human_required=False, graduation_status="not_eligible")
        return result
    result.update(stage="human_escalation", blockers=[], next_action="request_canonicalization_approval", assigned_agent="human", human_required=True, graduation_status="eligible_for_canonicalization", execution_status="ready_for_human_approval")
    return result


def build_state(evidence_root: Path = EVIDENCE_ROOT) -> dict[str, Any]:
    tracks = []
    for career_id, relative_path in EVIDENCE_PATHS.items():
        evidence = json.loads((evidence_root / relative_path).read_text(encoding="utf-8"))
        if evidence.get("career_id") != career_id:
            raise ValueError(f"career_id mismatch in {relative_path}")
        tracks.append(decide_next_action(import_candidate_evidence(evidence)))
    return {"schema_version": "career-track-state-v1", "generated_at": date.today().isoformat(), "tracks": tracks}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write the canonical generated snapshot")
    parser.add_argument("--check", action="store_true", help="verify the committed snapshot matches evidence")
    args = parser.parse_args()
    state = build_state()
    rendered = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not OUTPUT_PATH.exists() or OUTPUT_PATH.read_text(encoding="utf-8") != rendered:
            raise SystemExit("career-track state snapshot is not current")
        print("career-track state snapshot is current")
    elif args.write:
        OUTPUT_PATH.write_text(rendered, encoding="utf-8")
        print(OUTPUT_PATH)
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
