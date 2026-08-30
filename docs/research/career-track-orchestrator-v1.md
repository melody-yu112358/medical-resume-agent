# Career Expansion Orchestrator v1

This is governance tooling, not product runtime. It converts retained Candidate
evidence into a small, machine-readable dispatch contract so the next bounded
task is explicit rather than copied between Researcher, Candidate Builder,
Reviewer, Conformance, and Release Gate.

## Sources and generated state

- **Authoritative evidence:** `docs/research/role-validation/<career>/candidate-evidence-v1.json`.
- **Generated snapshot:** `docs/research/career-track-states-v1.json`; do not edit it by hand.
- **Schema:** `schemas/career-track-state.schema.json`.
- **Generator and policy:** `scripts/career_track_orchestrator.py`.

Refresh after a reviewed evidence change:

```powershell
python scripts/career_track_orchestrator.py --write
python scripts/career_track_orchestrator.py --check
```

The snapshot has one record per career, not one record per phase run. It records
coverage, personas, mappings, review and conformance status, blockers, next
action, the bounded agent role, human requirement, and remote-sync state.

## Deterministic policy

The policy follows `docs/ROLE_PACK_GRADUATION.md` without changing its gates:

1. Insufficient JD/company coverage routes to `researcher` with
   `collect_more_jds`.
2. Incomplete personas, mappings, or negative mappings routes to
   `candidate_builder` with `complete_candidate_assets`.
3. Unreviewed complete assets route to `reviewer`; review changes route to
   `implementer`.
4. A reviewed track with incomplete conformance routes to `conformance`.
5. Only a fully gate-satisfying synthetic/recorded state produces
   `eligible_for_canonicalization`, `request_canonicalization_approval`, and
   `human_required: true`. The tool never performs canonicalization.

`awaiting_remote_sync` is a recovery state: it produces `resume_remote_sync`
without recreating work, branches, or commits, as required by
`docs/REMOTE_SYNC_PROTOCOL.md`.

## Human escalation and dispatch boundary

The policy asks for a human only for canonicalization approval or a separately
declared policy/runtime/governance/security exception. Routine JD shortages,
ordinary review fixes, test failures, conformance shortages, and remote delays
remain machine-readable next actions.

The repository has no supported cross-session Codex dispatch connector in this
version. The generator **does not start agents**, create PRs, or access external
accounts. A later, separately approved connector may read `next_action` and
`assigned_agent`, then create a bounded Codex task through an approved task API;
it must retain the branch/PR and human-approval controls in `AGENTS.md` and the
remote-sync protocol.

## Current dry-run

CRA, CDM, Device Clinical/Application, and PV all resolve to:

`research → insufficient coverage → collect_more_jds → researcher → human_required: false`

Their Candidate evidence remains Beta and cannot become a canonical Pack or a
runnable target through this tool.
