"""Auditable GitHub dispatch-event consumer with a deliberately mockable task adapter."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from jsonschema import validate


REPOSITORY = "melody-yu112358/medical-resume-agent"
DISPATCH_ORIGIN = "career-dispatch-connector-v1"
CONSUMER_ORIGIN = "github-event-consumer-v1"
ALLOWED_DISPATCH_STATUSES = {"dispatch_created", "already_dispatched", "human_escalation_created"}
PROHIBITED_REQUIREMENTS = {
    "direct push to main", "auto merge", "auto canonicalize",
    "modify existing canonical Role Packs",
    "modify production runtime, workflow, routing, UI, Skill runtime, Claim Gate, or Confirmation Gate",
    "read, write, or commit secrets, tokens, or credentials",
}
ROOT = Path(__file__).resolve().parents[1]


class TaskAdapter(Protocol):
    def create_task(self, task_payload: dict[str, Any]) -> str:
        """Return a task reference only; it must not claim an agent has started."""


class MockTaskAdapter:
    """Test-only adapter with deterministic references and no external side effects."""

    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[dict[str, Any]] = []

    def create_task(self, task_payload: dict[str, Any]) -> str:
        self.calls.append(task_payload)
        if self.fail:
            raise OSError("mock task connector unavailable")
        return f"mock-codex-task:{task_payload['career_id']}:{len(self.calls)}"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _marker(digest: str) -> str:
    return f"<!-- career-dispatch-id:{digest} -->"


def _execution(dispatch: dict[str, Any], status: str, *, reference: str | None = None, error: str | None = None, started_at: str | None = None) -> dict[str, Any]:
    digest = dispatch.get("source_state_digest", "unknown")
    return {
        "schema_version": "codex-task-execution-record-v1",
        "source_state_digest": digest,
        "career_id": dispatch.get("career_id", "unknown"),
        "assigned_agent": dispatch.get("assigned_agent", "unknown"),
        "task_start_status": status,
        "task_reference": reference,
        "started_at": started_at,
        "attempt_id": f"attempt:{digest[:16]}",
        "last_error": error,
        "agent_started": False,
    }


def _contains_prohibited_requirement(payload: dict[str, Any]) -> bool:
    candidate_text = " ".join(str(payload.get(key, "")) for key in ("scope", "next_action", "assigned_agent"))
    return any(term.lower() in candidate_text.lower() for term in PROHIBITED_REQUIREMENTS)


def _validate_dispatch(event: dict[str, Any], dispatch: dict[str, Any]) -> str | None:
    try:
        validate(event, json.loads((ROOT / "schemas" / "github-dispatch-event.schema.json").read_text(encoding="utf-8")))
        validate(dispatch, json.loads((ROOT / "schemas" / "career-dispatch-record.schema.json").read_text(encoding="utf-8")))
    except Exception:
        return "invalid_schema"
    if event.get("event_name") != "issues" or event.get("repository") != REPOSITORY:
        return "invalid_event_repository"
    if event.get("origin") == CONSUMER_ORIGIN or "<!-- github-event-consumer-update -->" in str((event.get("issue") or {}).get("body") or ""):
        return "self_trigger"
    if event.get("origin") != DISPATCH_ORIGIN or event.get("action") not in {"opened", "reopened"}:
        return "untrusted_or_ignored_event"
    if dispatch.get("schema_version") != "career-dispatch-record-v1":
        return "invalid_dispatch_schema"
    if dispatch.get("dispatch_status") not in ALLOWED_DISPATCH_STATUSES:
        return "dispatch_not_consumable"
    digest = dispatch.get("source_state_digest")
    if not isinstance(digest, str) or _marker(digest) not in str((event.get("issue") or {}).get("body") or ""):
        return "stale_or_altered_digest"
    payload = dispatch.get("task_payload")
    if not isinstance(payload, dict) or payload.get("career_id") != dispatch.get("career_id") or payload.get("agent_started") is not False:
        return "invalid_task_payload"
    if bool(dispatch.get("human_required")) or bool(payload.get("human_required")):
        return "human_escalation"
    if _contains_prohibited_requirement(payload) or not PROHIBITED_REQUIREMENTS.issubset(set(payload.get("prohibited") or [])):
        return "prohibited_operation"
    return None


def consume_event(event: dict[str, Any], dispatch: dict[str, Any], records: dict[str, dict[str, Any]], adapter: TaskAdapter) -> dict[str, Any]:
    """Consume one event at most once; mutate only the caller-owned record map."""
    failure = _validate_dispatch(event, dispatch)
    if failure == "self_trigger":
        return _execution(dispatch, "self_trigger_ignored", error=failure)
    if failure == "human_escalation":
        return _execution(dispatch, "human_escalation_required", error=None)
    if failure:
        return _execution(dispatch, "rejected", error=failure)
    digest = dispatch["source_state_digest"]
    existing = records.get(digest)
    if existing and existing.get("task_start_status") == "codex_task_created":
        return {**existing, "task_start_status": "duplicate_ignored"}
    attempt = existing or _execution(dispatch, "task_start_failed", error="not_started")
    try:
        reference = adapter.create_task(dispatch["task_payload"])
    except OSError as exc:
        attempt.update(task_start_status="awaiting_remote_sync", last_error=type(exc).__name__)
        records[digest] = attempt
        return attempt
    except Exception as exc:
        attempt.update(task_start_status="task_start_failed", last_error=type(exc).__name__)
        records[digest] = attempt
        return attempt
    attempt.update(task_start_status="codex_task_created", task_reference=reference, started_at=_now(), last_error=None, agent_started=False)
    records[digest] = attempt
    return attempt
