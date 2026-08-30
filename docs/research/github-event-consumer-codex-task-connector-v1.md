# GitHub Event Consumer + Codex Task Connector v1

This is a governance/tooling contract. It consumes a GitHub `issues` event and
the corresponding persisted `career-dispatch-record-v1`; it does not recalculate
career readiness or change the Orchestrator policy.

## Contract and filtering

The consumer accepts only `opened` or `reopened` `issues` events from
`melody-yu112358/medical-resume-agent` with origin
`career-dispatch-connector-v1`. It validates both schemas, requires the stable
Issue marker to match the record's `source_state_digest`, and accepts only
`dispatch_created` / `already_dispatched` records.

It rejects malformed records, altered markers, unknown repositories, human
escalations, payloads that ask for prohibited operations, and payloads that
claim `agent_started`. Events tagged with the consumer origin or the consumer
writeback marker are `self_trigger_ignored`; Issue edits are ignored. This
prevents event → writeback → event loops.

## At-most-once execution

Execution records use `source_state_digest` as the stable key. The first
successful adapter call records `codex_task_created`; duplicate/replayed events
return `duplicate_ignored` and never call the adapter again. Adapter failure
keeps the same record and `attempt_id`, with `awaiting_remote_sync` or
`task_start_failed`; recovery reuses that record and digest rather than creating
a new branch, PR, or task record.

`human_required: true` produces `human_escalation_required` only and never calls
the adapter.

## Mock boundary

`MockTaskAdapter.create_task(task_payload)` is test-only and returns a mock task
reference. A created reference proves only `codex_task_created`:

`dispatch_created ≠ event_consumed ≠ codex_task_created ≠ agent_started`

No supported real GitHub-to-Codex task-start connector exists in this repository
or current environment. A future connector would need authenticated webhook
delivery, durable execution-record storage/locking, and an approved Codex
task-creation API. It must retain the existing branch/PR, human approval,
remote-sync, secret, and no-auto-merge safeguards.
