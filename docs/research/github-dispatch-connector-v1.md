# GitHub-backed Dispatch Connector v1

This governance/tooling connector consumes—rather than re-evaluates—the
generated `career-track-state-v1` snapshot. Its GitHub task is an Issue whose
body is a durable, machine-readable dispatch record.

## Inputs and record

For every track it reads `career_id`, `next_action`, `assigned_agent`,
`human_required`, `blockers`, and `execution_status`. The output follows
`schemas/career-dispatch-record.schema.json` and retains:

- `dispatch_status`;
- GitHub Issue URL (or `null` in dry-run);
- creation timestamp;
- stable source-state digest; and
- the bounded task payload.

The payload always names the career, action, assignee, scope, blockers, source
state version, and prohibited operations. It explicitly forbids direct `main`
pushes, auto-merge, auto-canonicalization, runtime/gate changes, and secret
handling.

## Operation

```powershell
# Read-only dry-run; default.
python scripts/github_dispatch_connector.py

# Create or reuse GitHub Issue dispatch records.
python scripts/github_dispatch_connector.py --apply
```

Each Issue body has `<!-- career-dispatch-id:<source-state-digest> -->`.
Before creating an Issue, the connector searches all issues for that exact
marker. A match returns `already_dispatched`; sequential repeat runs cannot
create a duplicate for the same state/action payload.

`human_required: false` produces a bounded agent task. `human_required: true`
produces only a human-escalation Issue; its payload still has
`agent_started: false` and the connector never starts work.

## Remote and execution boundaries

The connector never retries by recreating work. Any GitHub CLI/network failure
returns `dispatch_status: awaiting_remote_sync`, preserving the digest and
payload for a later `--apply` recovery, in line with
`docs/REMOTE_SYNC_PROTOCOL.md`.

Creating an Issue is **not** agent dispatch in the Codex runtime:

`dispatch_created ≠ agent_started`

There is no supported cross-session GitHub-to-Codex task-start connector in
this repository. A future separately approved integration would need an
authenticated GitHub event consumer plus a Codex task-creation connector that
reads this Issue payload, prevents duplicate task starts, and keeps existing
branch/PR/human-approval safeguards. This connector does not create branches,
PRs, merges, or canonical Role Packs.
