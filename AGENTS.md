# Multi-agent contribution guide

This repository is an evidence-bounded medical-career system. Agents and reviewers must preserve confirmed facts, responsibility limits, and the existing execution contract.

## Scope and ownership

- **Skill layer** (`skill-lite/medical-resume-skill/`) provides portable, human-readable guidance, fixtures, and validators. It translates confirmed experience; it never creates evidence or upgrades ownership.
- **Application/agent layer** (`src/medical_career_agent/`) implements the product workflow, schemas, gates, routing, and UI. Do not change this layer while working on role-pack research or governance unless the task explicitly requires a runtime change.
- **Canonical Role Packs** are the four JSON files in `data/role-packs/`: `clinical_research_v1`, `doctoral_v1`, `health_ai_data_v1`, and `medical_affairs_v1`. They are the single source of truth for their target semantics and execution guardrails. Preserve their current behavior unless a scoped, reviewed Role Pack change is explicitly requested.

## Generated artifacts

Never hand-edit `skill-lite/medical-resume-skill/references/role-packs.md` or `skill-lite/medical-resume-skill/references/role-pack-rules.json`. They are generated projections of the canonical Role Packs and schema. After an authorized canonical-pack change, regenerate them with `python scripts/generate_skill_role_pack_reference.py` and verify with `python scripts/generate_skill_role_pack_reference.py --check`.

## Evidence and boundary invariants

- Use only confirmed personal facts. Missing facts remain a question, gap, or conservative statement; public JD language is never personal evidence.
- A target may alter emphasis and ordering, never add facts or upgrade responsibility.
- Keep `explicit_gap`, `partial_match`, and negative mappings visible. In particular, coordination is not project/program ownership, and an internal academic presentation is not external, client, payer, or executive communication without direct evidence.
- Do not bypass or weaken the existing Confirmation Gate, Claim Gate, workflow contract, routing, UI, or schema protections.

## Role Pack research lifecycle

New target families begin as **Beta** research artifacts, not Canonical Role Packs. Follow the lifecycle and graduation evidence in `docs/ROLE_PACK_GRADUATION.md`. A Beta artifact must not alter the four stable packs or become routable/executable merely because its examples appear promising.

Real-JD research must retain traceable source snapshots/digests. Evaluate a fixed mix of positive, partial, and negative personas; run model-conformance checks separately from structural fixtures; and test prohibited claims and ownership boundaries as first-class requirements.

## Phase delivery protocol

For every phase, make the smallest scoped change and include:

1. Tests or validator runs appropriate to the changed artifact, including positive and negative/boundary cases.
2. A focused commit whose message identifies the phase and artifact.
3. Push the branch and create or update one pull request to `main`; that PR is the handoff record for Codex and human reviewers. Do not merge it automatically.
4. A PR report covering scope, files changed, commands/results, source and persona coverage, model-conformance results (if applicable), unresolved gaps, and an explicit statement of what was not changed.

## Remote sync recovery

All phases follow the [remote sync recovery protocol](docs/REMOTE_SYNC_PROTOCOL.md).
Treat a GitHub connection failure as a `remote sync delay`, not as a product,
test, or CI failure. Complete and verify local work first, then preserve its
single committed branch if remote synchronization fails.

After the first remote failure, make at most two short additional attempts.
If they fail, stop remote operations, record the required handoff details, and
report `execution_status: awaiting_remote_sync`. A later recovery may only
verify the existing commit, push the existing branch without force, and create
or update its intended PR. Do not create replacement branches or reimplement
the phase to work around network failures.

Every phase report must include one of the protocol's `execution_status`
values. Direct pushes to `main`, automatic merges, and unapproved force-pushes
remain prohibited.

## No scope creep

Do not refactor adjacent code, add dependencies, modify production behavior, or promote a target family while completing research, documentation, fixture, or evaluation work. If the requested change would affect runtime semantics, the four stable packs, routing, UI, `workflow-contract.json`, or either gate, stop and request a separately scoped task.

## Shared-account safety and merge controls

- Treat a shared ChatGPT/Codex account as an untrusted execution surface, not as a human identity or approval authority.
- Every agent change must use a dedicated branch and a pull request (PR) targeting `main`. Direct pushes to `main` are prohibited.
- Agents must never enable or request automatic merge. A merge requires an explicit decision by a traceable human GitHub account.
- Do not read, write, log, upload, or commit secrets, tokens, private keys, local credentials, credential files, or `.env` files. Stop and notify a human owner if any are encountered.
- Keep commits and PRs narrow. Do not mix governance changes with product, documentation, research, or generated-artifact changes.

## Role boundaries

- **Researcher** may research and report only. It must not modify production code, runtime configuration, or canonical Role Packs.
- **Implementer** may modify scoped code only on its dedicated branch, and must run the tests required by the changed surface before opening or updating a PR.
- **Reviewer** is read-only. It reviews the diff, tests, and evidence; it must not edit code, push commits, or merge.
- **Release Gate** is read-only. It reports `PASS` or `FAIL` with a merge recommendation; it must not merge, approve on behalf of a human, or change repository settings.

The detailed responsibilities and handoffs are in `agents/`.

## Governance-only PRs

The following paths are governance-sensitive:

- `.github/workflows/**`
- `AGENTS.md`
- `agents/**`
- `docs/AGENT_GOVERNANCE.md`
- files that affect permissions, repository governance, or release controls

Any change to a governance-sensitive path must be in a standalone governance PR. That PR may not modify product code, canonical Role Packs, schemas, workflow contracts, generated Role Pack references, or product behavior. Conversely, non-governance PRs must not change governance-sensitive paths.

## Required handoff record

Each PR must state its scope, files changed, verification performed, known gaps, and explicit non-goals. The PR is a handoff record, not merge authorization. See `docs/AGENT_GOVERNANCE.md` for the human-owned GitHub settings that cannot be enforced by repository files alone.
