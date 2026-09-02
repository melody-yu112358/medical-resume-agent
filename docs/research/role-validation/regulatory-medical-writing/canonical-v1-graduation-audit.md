# Regulatory Medical Writing — Candidate to Canonical v1 domain graduation audit

**Audited Candidate head:** `c5c0c3c`  
**Audit date:** 2026-09-02  
**Model conformance:** `pending` — not assessed here and not a domain-graduation blocker.

| Canonical v1 domain criterion | Result | Evidence |
| --- | --- | --- |
| JD/company coverage | PASS | 8 qualifying China-market JDs across 8 employers; two historical records are explicitly excluded. |
| Provenance and digest reproducibility | PASS | Every qualifying snapshot retains a saved source extract and deterministic SHA-256 digest. |
| Stable core versus JD-dependent separation | PASS | Controlled clinical-document support is stable; strategy, submission, client/program, authority communication, complex lead authorship and management are excluded. |
| Persona and multi-employer exercise | PASS | 8 fixed personas; each maps to at least 3 qualifying JDs from distinct employers. |
| Mapping and negative boundaries | PASS | Direct/transferable/partial/gap mappings and four machine-readable negative rules block known ownership inflation. |
| Auditable domain evaluation | PASS | 4 fixed direct/transferable/partial/gap cases across 4 employers; median usefulness 4/5. |
| Factuality and ownership | PASS | All evaluated cases are PASS; participation, support, review, and exposure remain bounded. |
| Critical unsupported claims | PASS | 0 in the recorded domain-evaluation cases; no unassessed case is represented as zero. |
| Regression/invariant status | PASS | Candidate provenance, persona diversity, and domain-evaluation tests pass; full regression passes. |
| Single-employer overfit | PASS | Stable core and fixed cases span more than one employer and more than one JD. |

## Decision

`eligible_for_canonicalization`  
`human_required=true`

The Candidate has satisfied the **domain** evidence and static-evaluation gates
for a narrowly scoped Canonical v1 promotion proposal. This decision does not
create a canonical JSON, route the target, invoke a model, or authorize merge.
A traceable human must separately approve any Canonical v1 promotion PR.

## Explicit limitation

`Cross-model validated` remains pending. It requires separately recorded model
identity/configuration, prompts, inputs/outputs, and conformance audits; it is
not claimed or inferred by this domain audit.
