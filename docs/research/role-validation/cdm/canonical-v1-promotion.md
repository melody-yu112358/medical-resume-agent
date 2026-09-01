# CDM Canonical v1 promotion record

## Scope

This promotion adds `clinical_data_management_v1` as a canonical source. It
does not change routing, runtime, workflow contracts, UI, Claim Gate,
Confirmation Gate, graduation policy, or existing Role Pack semantics.

## Evidence and domain validation

- Candidate evidence is recorded in
  `docs/research/role-validation/cdm/candidate-evidence-v1.json`.
- Coverage: 8 qualifying China-market JD snapshots across 8 employers. Each
  countable record retains a reproducible `sha256(url + LF + source_snapshot)`
  digest scope; search extracts remain explicitly non-qualifying.
- Fixed personas cover positive, transferable, partial, and negative fits
  across multiple JDs and employers.
- Stable core: bounded trial-data checking/cleaning, query or discrepancy
  follow-up, controlled data-management documentation, GCP/SOP-aligned
  quality/confidentiality support, data-issue coordination, and data-review or
  reconciliation support within confirmed scope.
- JD-dependent/senior scope is excluded: database-lock, final delivery,
  budget/bid/client/vendor ownership, staff management, EDC-build authority,
  specialist coding/programming, and final quality accountability.
- Domain evaluation records median usefulness 4/5, factuality `PASS`,
  ownership `PASS`, and 0 critical unsupported claims.

## Guardrails

Data cleaning/review is not database-lock or final-delivery ownership. CRF or
EDC support is not CRF design or EDC-build authority. General analysis is not
clinical-trial CDM, GCP, or EDC experience. Support and issue coordination are
not project, client, vendor, budget, or team-management ownership.

## Verification and limitations

The canonical JSON is schema-validated; generated Skill projections are
derived only through `generate_skill_role_pack_reference.py`. Positive,
transferable, partial, and negative cases are included in the canonical source
and checked by targeted/invariant tests.

Cross-model validation is `pending/not yet performed`; no model ID, provider
configuration, or cross-model conformance outcome is claimed. This is not a
Canonical v1 domain-validation failure.

## Non-goals

No runtime integration, automatic merge, or modification to another Role Pack
is included. Final retention requires traceable human GitHub approval.
