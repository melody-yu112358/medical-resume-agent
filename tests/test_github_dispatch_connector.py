from __future__ import annotations

import json
from pathlib import Path

from jsonschema import validate

from scripts.github_dispatch_connector import DEFAULT_STATE, REPOSITORY, build_record, dispatch_state, dispatch_track, issue_marker


def _track(*, human_required: bool = False) -> dict:
    return {
        "career_id": "clinical_research_associate", "next_action": "collect_more_jds",
        "assigned_agent": "researcher", "human_required": human_required,
        "blockers": ["insufficient_jd_coverage"], "execution_status": "completed_local",
    }


def test_dry_run_builds_a_bounded_researcher_task_without_starting_an_agent():
    record = dispatch_track(_track(), "career-track-state-v1", apply=False)

    assert record["dispatch_status"] == "planned"
    assert record["task_reference"] is None
    assert record["task_payload"]["assigned_agent"] == "researcher"
    assert record["task_payload"]["next_action"] == "collect_more_jds"
    assert record["task_payload"]["agent_started"] is False
    assert "auto merge" in record["task_payload"]["prohibited"]


def test_apply_is_idempotent_for_the_same_source_state_digest():
    created: list[dict] = []

    def runner(arguments: list[str]) -> str:
        if arguments[:2] == ["issue", "list"]:
            return json.dumps(created)
        if arguments[:2] == ["issue", "create"]:
            body = arguments[arguments.index("--body") + 1]
            created.append({"number": 41, "url": "https://github.test/issues/41", "body": body})
            return "https://github.test/issues/41"
        raise AssertionError(arguments)

    first = dispatch_track(_track(), "career-track-state-v1", apply=True, runner=runner)
    second = dispatch_track(_track(), "career-track-state-v1", apply=True, runner=runner)

    assert first["dispatch_status"] == "dispatch_created"
    assert second["dispatch_status"] == "already_dispatched"
    assert len(created) == 1
    assert issue_marker(first) in created[0]["body"]


def test_digest_changes_when_source_track_state_changes_without_a_new_action():
    original = build_record(_track(), "career-track-state-v1")
    changed = _track()
    changed["conformance_status"] = "in_progress"
    changed["execution_status"] = "review_pending"

    updated = build_record(changed, "career-track-state-v1")

    assert updated["next_action"] == original["next_action"]
    assert updated["source_state_digest"] != original["source_state_digest"]


def test_every_github_issue_command_binds_the_configured_repository():
    calls: list[list[str]] = []

    def runner(arguments: list[str]) -> str:
        calls.append(arguments)
        if arguments[:2] == ["issue", "list"]:
            return "[]"
        return "https://github.test/issues/43"

    dispatch_track(_track(), "career-track-state-v1", apply=True, runner=runner)

    assert len(calls) == 2
    assert all("--repo" in call and call[call.index("--repo") + 1] == REPOSITORY for call in calls)


def test_human_required_creates_escalation_only_and_never_starts_an_agent():
    calls: list[list[str]] = []

    def runner(arguments: list[str]) -> str:
        calls.append(arguments)
        if arguments[:2] == ["issue", "list"]:
            return "[]"
        return "https://github.test/issues/42"

    record = dispatch_track(_track(human_required=True), "career-track-state-v1", apply=True, runner=runner)

    assert record["dispatch_status"] == "human_escalation_created"
    assert record["task_payload"]["assigned_agent"] == "human"
    assert record["task_payload"]["next_action"] == "human_escalation"
    assert record["task_payload"]["agent_started"] is False
    assert all("codex" not in " ".join(call).lower() for call in calls)


def test_remote_failure_is_an_awaiting_remote_sync_record():
    def failing_runner(arguments: list[str]) -> str:
        raise OSError("network unavailable")

    record = dispatch_track(_track(), "career-track-state-v1", apply=True, runner=failing_runner)

    assert record["dispatch_status"] == "awaiting_remote_sync"
    assert record["task_reference"] is None
    assert record["last_remote_error"] == "OSError"


def test_current_track_dry_run_reflects_evidence_driven_next_actions():
    state = json.loads(DEFAULT_STATE.read_text(encoding="utf-8"))
    schema = json.loads((Path(__file__).parents[1] / "schemas" / "career-dispatch-record.schema.json").read_text(encoding="utf-8"))

    records = dispatch_state(state, apply=False)

    assert len(records) == 4
    assert all(record["dispatch_status"] == "planned" for record in records)
    payloads = {record["career_id"]: record["task_payload"] for record in records}
    expected_tasks = {
        "clinical_research_associate": ("conformance", "run_conformance"),
        "clinical_data_management": ("conformance", "run_conformance"),
        "medical_device_clinical_application_specialist": ("conformance", "run_conformance"),
        "pharmacovigilance_drug_safety": ("conformance", "run_conformance"),
    }
    assert {
        career_id: (payload["assigned_agent"], payload["next_action"])
        for career_id, payload in payloads.items()
    } == expected_tasks
    for record in records:
        validate(instance=record, schema=schema)
