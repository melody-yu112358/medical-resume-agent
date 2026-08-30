"""GitHub-Issue-backed, idempotent Career Track dispatch connector.

The connector consumes the state contract.  It deliberately does not determine
career readiness, start Codex, create branches, merge, or canonicalize.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATE = ROOT / "docs" / "research" / "career-track-states-v1.json"
REPOSITORY = "melody-yu112358/medical-resume-agent"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _digest(value: Any) -> str:
    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _semantic_track_state(track: dict[str, Any]) -> dict[str, Any]:
    """Digest the complete dispatch-relevant source track, not presentation time."""
    return {
        key: value for key, value in track.items()
        if key not in {"generated_at", "created_at", "updated_at"}
    }


def task_payload(track: dict[str, Any], state_version: str) -> dict[str, Any]:
    human = bool(track["human_required"])
    scope = (
        "Collect and retain traceable, current or recent public JD evidence for this Career Candidate. "
        "Do not infer personal experience from JDs."
        if track["next_action"] == "collect_more_jds"
        else "Perform only the bounded next action described by the source Career Track State."
    )
    return {
        "career_id": track["career_id"],
        "assigned_agent": "human" if human else track["assigned_agent"],
        "next_action": "human_escalation" if human else track["next_action"],
        "scope": scope,
        "blockers": list(track.get("blockers") or []),
        "source_state_version": state_version,
        "prohibited": [
            "direct push to main", "auto merge", "auto canonicalize",
            "modify existing canonical Role Packs", "modify production runtime, workflow, routing, UI, Skill runtime, Claim Gate, or Confirmation Gate",
            "read, write, or commit secrets, tokens, or credentials",
        ],
        "human_required": human,
        "agent_started": False,
    }


def build_record(track: dict[str, Any], state_version: str, *, status: str = "planned", task_reference: str | None = None, error: str | None = None) -> dict[str, Any]:
    payload = task_payload(track, state_version)
    source_digest = _digest({"state_version": state_version, "track": _semantic_track_state(track)})
    return {
        "schema_version": "career-dispatch-record-v1",
        "career_id": track["career_id"],
        "next_action": track["next_action"],
        "assigned_agent": track["assigned_agent"],
        "human_required": bool(track["human_required"]),
        "dispatch_status": status,
        "task_reference": task_reference,
        "created_at": _utc_now(),
        "source_state_digest": source_digest,
        "task_payload": payload,
        "last_remote_error": error,
    }


def issue_marker(record: dict[str, Any]) -> str:
    return f"<!-- career-dispatch-id:{record['source_state_digest']} -->"


def issue_body(record: dict[str, Any]) -> str:
    kind = "Human escalation" if record["human_required"] else "Bounded agent task"
    payload = json.dumps(record["task_payload"], ensure_ascii=False, indent=2)
    return f"# {kind}\n\n{issue_marker(record)}\n\n```json\n{payload}\n```\n\n`dispatch_created` records task creation only. It does not mean `agent_started`.\n"


def _run_gh(arguments: list[str]) -> str:
    result = subprocess.run(["gh", *arguments], check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _find_existing(record: dict[str, Any], runner: Callable[[list[str]], str]) -> dict[str, Any] | None:
    marker = issue_marker(record)
    raw = runner(["issue", "list", "--repo", REPOSITORY, "--state", "all", "--search", f'"{marker}" in:body', "--json", "number,url,body", "--limit", "100"])
    for issue in json.loads(raw or "[]"):
        if marker in str(issue.get("body") or ""):
            return issue
    return None


def dispatch_track(track: dict[str, Any], state_version: str, *, apply: bool, runner: Callable[[list[str]], str] = _run_gh) -> dict[str, Any]:
    record = build_record(track, state_version)
    if not apply:
        return record
    try:
        existing = _find_existing(record, runner)
        if existing:
            record["dispatch_status"] = "already_dispatched"
            record["task_reference"] = existing.get("url") or f"issue:{existing.get('number')}"
            return record
        title_prefix = "[human-escalation]" if record["human_required"] else "[career-dispatch]"
        title = f"{title_prefix} {record['career_id']}: {record['task_payload']['next_action']}"
        reference = runner(["issue", "create", "--repo", REPOSITORY, "--title", title, "--body", issue_body(record)])
        record["dispatch_status"] = "human_escalation_created" if record["human_required"] else "dispatch_created"
        record["task_reference"] = reference
        return record
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        record["dispatch_status"] = "awaiting_remote_sync"
        record["last_remote_error"] = type(exc).__name__
        return record


def dispatch_state(state: dict[str, Any], *, apply: bool, runner: Callable[[list[str]], str] = _run_gh) -> list[dict[str, Any]]:
    version = str(state["schema_version"])
    return [dispatch_track(track, version, apply=apply, runner=runner) for track in state.get("tracks", [])]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--apply", action="store_true", help="create/reuse GitHub Issue records; default is dry-run")
    args = parser.parse_args()
    state = json.loads(args.state.read_text(encoding="utf-8"))
    print(json.dumps(dispatch_state(state, apply=args.apply), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
