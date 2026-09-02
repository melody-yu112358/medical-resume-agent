# Documentation and source-of-truth index

This index assigns one responsibility to each long-lived documentation class.
It is an index, not a replacement for the linked source.

| Classification | Responsibility | Current sources |
| --- | --- | --- |
| AUTHORITATIVE | Current rules or machine-readable contracts that govern behavior. | `AGENTS.md`; `agents/*.md`; `docs/ROLE_PACK_GRADUATION.md`; `docs/REMOTE_SYNC_PROTOCOL.md`; `docs/AGENT_GOVERNANCE.md`; `data/role-packs/*.json`; `schemas/role-pack.schema.json`; `skill-lite/medical-resume-skill/SKILL.md`; `references/evidence-rules.md`; `references/workflow-contract.json` |
| GENERATED | Projection of canonical inputs; never hand-edit. | `references/role-packs.md`; `references/role-pack-rules.json` |
| EVAL_EVIDENCE | Reproducible validation, JD provenance, synthetic cases, and regression baselines; does not itself change runtime behavior. | Clinical Operations snapshots, domain review, and conformance ledger; `data/evaluations/**`; `data/fixtures/**`; `tests/fixtures/**`; `references/phase-*.json` |
| HISTORICAL | Traceability or prior decision context; never a current operating rule. | `docs/BUILD_LOG.md`; `docs/audits/**`; `docs/ROLE_VALIDATION_CANDIDATE_MATURITY.md`; early architecture and LLM planning records |
| REFERENCE | Product, research, or implementation explanation that defers to an authoritative source on conflict. | `README*`; current product documents; v2 planning documents; research guides |

## Conflict resolution

1. Runtime targets and canonical Pack semantics come from
   `workflow-contract.json` and `data/role-packs/*.json`, not a prose count.
2. Role Pack graduation comes only from `ROLE_PACK_GRADUATION.md`.
3. Remote synchronization comes only from `REMOTE_SYNC_PROTOCOL.md`.
4. Generated Role Pack references are regenerated from their canonical inputs.
5. Historical and evaluation evidence may explain a decision but cannot change
   a runtime contract or governance rule.
6. `docs/CAREER_ROLE_PACK_LANDSCAPE.md` is the current Chinese overview and
   roadmap entry. It defers to canonical JSON, graduation policy, and
   role-validation evidence on any status conflict; `docs/research/china-career-coverage-matrix-v1.md`
   remains the planning source for coverage tiers and heuristic estimates.

No Phase artifact, Clinical Operations evidence path, or test fixture is moved
or renamed by this index.
