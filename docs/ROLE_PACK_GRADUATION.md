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
| Canonical v1 (domain validated) | A reviewed JSON Role Pack whose stable occupational semantics, evidence mappings, and boundary rules have passed domain validation. | Canonical source under the existing contract. Routing/execution support remains a separately scoped runtime decision; canonicalization does not silently add it. |
| Cross-model validated | A Canonical v1 Pack whose model-execution behavior has also passed a reproducible, multi-model conformance program. | A post-canonical hardening status; it does not alter the Pack's domain semantics. |

Promotion is sequential. Domain validation and model-conformance validation are distinct: neither label substitutes for its own criteria, and a Canonical v1 promotion must be an explicit PR decision. Model conformance is important release hardening, but it does not determine whether a role family's occupational knowledge is stable.

## Validation dimensions

### Domain validation

Domain validation establishes whether the Pack expresses stable career semantics rather than one employer's wording. It evaluates JD provenance and coverage, stable versus JD-dependent responsibilities, fixed confirmed personas, evidence mappings, negative mappings, usefulness, and factual and ownership boundaries. Its evidence is portable because it concerns the Pack's content, not a particular model deployment.

### Model-conformance validation

Model-conformance validation establishes whether one or more host-model executions preserve the Pack's domain boundaries. It evaluates exact model and configuration provenance, prompts and outputs, model-version regressions, unsupported-claim rates, and consistency across model versions. It must never be used to weaken the Pack's factuality, ownership, or critical-claim rules.

## Graduation criteria

### Beta → Candidate

- At least 8 current or recent, traceable public JDs from at least 5 companies across 3 responsibility levels or company types.
- A documented stable core; employer- or level-specific requirements are explicitly separated as JD-dependent.
- At least 8 fixed confirmed personas, including at least 3 clear negative/partial personas. Each is exercised against at least 3 JDs in the candidate cluster.
- Machine-readable positive, partial, gap, and negative-mapping fixtures. Negative rules must block ownership, client/external communication, commercial/payer, or management claims absent direct evidence.
- No semantic change to the existing four canonical packs or runtime paths.

### Candidate → Canonical v1 (domain validated)

- Reproducible domain tests validate fixture structure, source provenance, fact references, prohibited claims, ownership preservation, and stable negative mappings.
- Stable evidence mappings and explicit gaps work across the fixed positive, partial, and negative personas and more than one JD. A Pack depending mainly on one employer's vocabulary remains Beta/Candidate.
- Domain-reviewed evaluation cases achieve a median usefulness/resume-quality score of at least 4/5. A merely safe but generic output does not pass.
- Domain audits show 0 critical unsupported claims. Factuality and ownership preservation remain mandatory: participation is not rewritten as ownership, leadership, management, independent delivery, external/client/executive communication, or other unsupported scope.
- A narrowly scoped PR adds or changes the canonical JSON Pack, schema-valid positive, partial, and negative evaluation cases, and only the generated projections required by that canonical input.
- Contract, reference-generation, targeted new-Pack, and practical full regression tests pass. Review confirms target scope, allowed/restricted wording, forbidden claims, required evidence, and explicit non-claims remain compatible with the existing Claim Gate and routing contract.
- The PR documents sources, personas, domain-evaluation method and scores, tests, limitations, the current model-conformance status, and confirms no change to the four pre-existing Role Packs' execution semantics.
- A traceable human reviewer approves the promotion. Automation must not merge it.

### Canonical v1 → Cross-model validated

- At least 30 isolated model-conformance runs across at least 2 identifiable model versions, with factuality and ownership-preservation averages of at least 4.5/5.
- Every run retains the exact model ID, reasoning/configuration, prompt, input, output, Skill source digest, JD snapshot digest, persona ID, scores, unsupported-claim audit, and reviewer decision.
- The cross-model audit shows 0 critical unsupported claims and fewer than 2% noncritical unsupported claims. A critical factuality or ownership failure fails this status regardless of averages.
- Median usefulness/resume-quality remains at least 4/5 across the recorded runs, and the Pack remains useful and truthful across more than one JD.
- Model-version regression runs repeat when the Pack prompt, Pack rules, or a host-model version changes. Any regression failure is a release-hardening issue, not evidence to rewrite or weaken the Pack's domain boundaries.

## Phase and PR handoff checklist

Each phase is a small, reviewable commit. Before push, run the relevant tests and validators; include both positive and negative cases. Push the working branch and create or update a single PR against `main`. Use that PR—not an undocumented chat summary—as the shared Codex/reviewer handoff point.

The PR description must state:

1. phase goal and precise scope;
2. changed files and whether any are generated;
3. commands run and results;
4. JD provenance/coverage, persona mix, and domain-evaluation coverage;
5. current cross-model-validation status, if any, without presenting pending work as a domain-validation failure;
6. negative mappings, gaps, and unresolved risks;
7. explicit non-goals, including any untouched runtime contracts.

Do not broaden a research or documentation phase into UI, routing, contract, gate, schema, or existing-Pack work. Open a separately scoped task if any of those changes become necessary.
