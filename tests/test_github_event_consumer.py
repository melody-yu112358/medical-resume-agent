from __future__ import annotations

import json
from pathlib import Path

from jsonschema import validate

from scripts.github_dispatch_connector import build_record, issue_body
from scripts.github_event_consumer import CONSUMER_ORIGIN, DISPATCH_ORIGIN, MockTaskAdapter, REPOSITORY, consume_event


ROOT = Path(__file__).parents[1]


def _dispatch(*, human_required: bool = False) -> dict:
    track = {
        "career_id": "clinical_research_associate", "next_action": "collect_more_jds",
        "assigned_agent": "researcher", "human_required": human_required,
        "blockers": ["insufficient_jd_coverage"], "execution_status": "completed_local",
    }
    record = build_record(track, "career-track-state-v1")
    record["dispatch_status"] = "dispatch_created" if not human_required else "human_escalation_created"
    return record


def _event(dispatch: dict, *, action: str = "opened", origin: str = DISPATCH_ORIGIN, body: str | None = None) -> dict:
    return {"event_name": "issues", "action": action, "repository": REPOSITORY, "origin": origin, "issue": {"number": 101, "body": body or issue_body(dispatch)}}


def test_valid_cra_research_dispatch_starts_mock_task_once():
    dispatch = _dispatch()
    records: dict[str, dict] = {}
    adapter = MockTaskAdapter()

    result = consume_event(_event(dispatch), dispatch, records, adapter)

    assert result["task_start_status"] == "codex_task_created"
    assert result["task_reference"].startswith("mock-codex-task:clinical_research_associate")
    assert result["agent_started"] is False
    assert len(adapter.calls) == 1
    schema = json.loads((ROOT / "schemas" / "codex-task-execution-record.schema.json").read_text(encoding="utf-8"))
    validate(instance=result, schema=schema)


def test_duplicate_or_replayed_event_never_starts_a_second_task():
    dispatch, records, adapter = _dispatch(), {}, MockTaskAdapter()
    consume_event(_event(dispatch), dispatch, records, adapter)

    duplicate = consume_event(_event(dispatch, action="reopened"), dispatch, records, adapter)

    assert duplicate["task_start_status"] == "duplicate_ignored"
    assert len(adapter.calls) == 1


def test_altered_digest_malformed_event_and_prohibited_operation_are_rejected():
    dispatch, adapter = _dispatch(), MockTaskAdapter()
    altered = _event(dispatch, body="# Bounded agent task\n<!-- career-dispatch-id:forged -->")
    assert consume_event(altered, dispatch, {}, adapter)["task_start_status"] == "rejected"

    malformed = _event(dispatch)
    malformed["repository"] = "other/repo"
    assert consume_event(malformed, dispatch, {}, adapter)["task_start_status"] == "rejected"

    forbidden = _dispatch()
    forbidden["task_payload"]["scope"] = "Please direct push to main."
    assert consume_event(_event(forbidden), forbidden, {}, adapter)["task_start_status"] == "rejected"
    assert not adapter.calls


def test_human_escalation_and_self_trigger_never_call_adapter():
    adapter = MockTaskAdapter()
    human = _dispatch(human_required=True)
    human_result = consume_event(_event(human), human, {}, adapter)
    self_result = consume_event(_event(_dispatch(), origin=CONSUMER_ORIGIN), _dispatch(), {}, adapter)

    assert human_result["task_start_status"] == "human_escalation_required"
    assert self_result["task_start_status"] == "self_trigger_ignored"
    assert not adapter.calls


def test_adapter_failure_reuses_the_same_execution_record_for_recovery():
    dispatch, records = _dispatch(), {}
    failed = consume_event(_event(dispatch), dispatch, records, MockTaskAdapter(fail=True))
    failed_status = failed["task_start_status"]
    attempt_id = failed["attempt_id"]
    recovered = consume_event(_event(dispatch, action="reopened"), dispatch, records, MockTaskAdapter())

    assert failed_status == "awaiting_remote_sync"
    assert recovered["task_start_status"] == "codex_task_created"
    assert attempt_id == recovered["attempt_id"]


def test_current_four_dispatches_map_to_researcher_contracts_without_external_starts():
    state = json.loads((ROOT / "docs" / "research" / "career-track-states-v1.json").read_text(encoding="utf-8"))
    from scripts.github_dispatch_connector import dispatch_state

    dispatches = dispatch_state(state, apply=False)
    assert len(dispatches) == 4
    assert all(item["task_payload"]["assigned_agent"] == "researcher" for item in dispatches)
    assert all(item["task_payload"]["agent_started"] is False for item in dispatches)
