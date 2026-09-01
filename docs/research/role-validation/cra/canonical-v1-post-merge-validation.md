# CRA Canonical v1 post-merge validation

## Scope

This record validates the already-merged `clinical_research_associate_v1`
canonical source. It does not alter the Role Pack, runtime, routing, workflow
contract, Claim Gate, Confirmation Gate, UI, or graduation policy.

## Traceability

- Candidate evidence: PR [#91](https://github.com/melody-yu112358/medical-resume-agent/pull/91),
  `ac344d8`.
- Candidate evidence coverage: 8 qualifying China-market JD snapshots from 6
  employers; the two pending IQVIA leads are not counted.
- Domain-evaluation source:
  `docs/research/role-validation/cra/domain-evaluation-v1.json`.
- Canonical source:
  `data/role-packs/clinical_research_associate_v1.json`.
- Canonical source SHA-256:
  `15491449af2de58aa4fc0d52d2406f183449fb5665ac6a9a1f4a00dd8420fe0e`.
- Ancestry incident: `37ae49e` (`test(release): add frozen regression
  baseline`) had `5190ef1` (`feat(role-pack): prepare CRA canonical v1`) as
  its parent. The CRA Pack therefore entered `main` through PR #95's branch
  ancestry, rather than through a separately reviewed CRA promotion PR.
  `37ae49e` itself is not treated as the semantic source of the Pack.

## Domain validation result

The canonical Pack retains the Candidate stable core: bounded research
execution support, study documentation/CRF maintenance, missing-data and query
follow-up, GCP-aligned process support, and internal research-team
coordination. It does not adopt JD-specific senior scope.

- Fixed personas and the canonical positive, partial, and negative cases are
  evidence-bound.
- Domain evaluation has four direct/transferable/partial/gap cases across four
  JD snapshots. Median usefulness is 4/5.
- Factuality: `PASS`.
- Ownership preservation: `PASS`.
- Critical unsupported claims: `0`.
- Boundaries remain explicit: documentation or CRF support is not independent
  monitoring, site-lifecycle ownership, recruitment, budget, project/program,
  PI/sponsor/external communication, team-management, or compliance ownership.

## Verification

Run on the post-merge `main` baseline:

```text
CRA role-pack schema validation passed
python scripts/generate_skill_role_pack_reference.py --check
30 targeted tests passed
418 full pytest tests passed
```

The generator check confirms the committed Skill projections already match the
canonical JSON. Existing canonical Role Pack execution-invariant tests passed;
this validation did not rewrite any existing Pack or generated artifact.

## Limitations and approval

- Cross-model validation is `pending/not yet performed`; it is not a Canonical
  v1 domain-validation failure.
- No model result, model ID, provider configuration, or cross-model claim-rate
  is asserted here.
- Post-merge human approval is **pending**. A shared ChatGPT/Codex account is
  not an approval identity. A traceable human GitHub account must review this
  validation PR and explicitly decide whether to retain the already-merged
  canonical source.

## Non-goals

No new CRA Role Pack is created, no existing Role Pack is rewritten, and no
runtime integration or automatic merge is performed.
