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

## No scope creep

Do not refactor adjacent code, add dependencies, modify production behavior, or promote a target family while completing research, documentation, fixture, or evaluation work. If the requested change would affect runtime semantics, the four stable packs, routing, UI, `workflow-contract.json`, or either gate, stop and request a separately scoped task.
