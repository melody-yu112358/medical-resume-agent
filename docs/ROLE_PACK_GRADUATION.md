# Role Pack graduation

This document defines how a researched target family becomes an executable canonical Role Pack. It protects the existing canonical set: `clinical_research_v1`, `doctoral_v1`, `health_ai_data_v1`, and `medical_affairs_v1`.

Those four packs remain stable. Research for another target family must not change their execution semantics, routing, UI, Claim Gate, or `workflow-contract.json`.

## Source of truth and artifact flow

Canonical packs live only in `data/role-packs/*.json` and are validated against `schemas/role-pack.schema.json`. The Skill reference files `references/role-packs.md` and `references/role-pack-rules.json` are generated projections, never an editing surface. After an authorized canonical change:

```powershell
python scripts/generate_skill_role_pack_reference.py
python scripts/generate_skill_role_pack_reference.py --check
```

The generated artifacts must be committed with the canonical input change.

## Maturity states

| State | Meaning | Execution status |
| --- | --- | --- |
| Beta | Research hypothesis with machine-readable fixtures and explicit uncertainty. | Not canonical; not routable/executable. |
| Candidate | Beta evidence meets the required coverage and is ready for independent review. | Still not canonical or routable. |
| Validated | Candidate has passed reproducible review and regression checks. | May be proposed in a separate, scoped canonicalization PR. |
| Canonical | Reviewed JSON Role Pack in `data/role-packs/`, with generated projections current. | Executable under the existing Role Pack contract. |

Promotion is sequential. No state label substitutes for passing the criteria below, and a Canonical promotion must be an explicit PR decision.

## Graduation criteria

### Beta → Candidate

- At least 8 current or recent, traceable public JDs from at least 5 companies across 3 responsibility levels or company types.
- A documented stable core; employer- or level-specific requirements are explicitly separated as JD-dependent.
- At least 8 fixed confirmed personas, including at least 3 clear negative/partial personas. Each is exercised against at least 3 JDs in the candidate cluster.
- Machine-readable positive, partial, gap, and negative-mapping fixtures. Negative rules must block ownership, client/external communication, commercial/payer, or management claims absent direct evidence.
- No semantic change to the existing four canonical packs or runtime paths.

### Candidate → Validated

- Reproducible tests validate fixture structure, provenance, fact references, prohibited claims, and ownership preservation.
- At least 30 isolated model-conformance runs across 2 model versions, with factuality and ownership-preservation averages of at least 4.5/5 and no critical unsupported ownership claim.
- Median usefulness/resume-quality score of at least 4/5. A merely safe but generic output does not pass.
- Final audits show 0 critical unsupported claims and fewer than 2% noncritical unsupported claims.
- The stable core yields useful, truthful output from more than one JD; a pack depending mainly on a single employer's vocabulary remains Beta/Candidate.

### Validated → Canonical

- A narrowly scoped PR adds or changes the canonical JSON pack, schema-valid evaluation cases, and only the generated projections required by that input.
- Contract, reference-generation, and targeted new-pack tests pass; full regression coverage is run when practical and reported.
- Review confirms target scope, allowed/restricted wording, forbidden claims, required evidence, and explicit non-claims are compatible with the existing Claim Gate and routing contract.
- The PR documents sources, personas, model runs, test results, limitations, and confirms no change to the four pre-existing Role Packs' execution semantics.
- A human reviewer approves the promotion. Automation must not merge it.

## Phase and PR handoff checklist

Each phase is a small, reviewable commit. Before push, run the relevant tests and validators; include both positive and negative cases. Push the working branch and create or update a single PR against `main`. Use that PR—not an undocumented chat summary—as the shared Codex/reviewer handoff point.

The PR description must state:

1. phase goal and precise scope;
2. changed files and whether any are generated;
3. commands run and results;
4. JD provenance/coverage, persona mix, and model-conformance coverage;
5. negative mappings, gaps, and unresolved risks;
6. explicit non-goals, including any untouched runtime contracts.

Do not broaden a research or documentation phase into UI, routing, contract, gate, schema, or existing-Pack work. Open a separately scoped task if any of those changes become necessary.
