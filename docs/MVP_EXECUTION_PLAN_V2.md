# Unbounded v2 MVP Execution Plan

## Delivery principle

Each sprint adds one coherent part of the Evidence → Hypothesis → Reality → Action → New Evidence loop. Existing functionality remains available; the v2 work is additive and no sprint should require a broad UI refactor.

## Sprint 0 — Documentation alignment

**Goal:** Establish the shared product, domain, technical, AI, and delivery baseline.

**Files changed:**

- `docs/PRODUCT_HANDBOOK_V2.md`
- `docs/USER_JOURNEY_V2.md`
- `docs/DOMAIN_MODEL_V2.md`
- `docs/TECHNICAL_DESIGN_V2.md`
- `docs/AI_SYSTEM_V2.md`
- `docs/MVP_EXECUTION_PLAN_V2.md`

**Acceptance criteria:** all six documents exist; P0/P1/P2 scope is explicit; the evidence verification rule and AI boundaries are unambiguous; MVP success measures and the Evidence Progress north-star metric are defined; v2 documentation precedence and legacy-document migration rules are explicit; no application code or current UI is changed.

## Sprint 1 — Domain models

**Goal:** Implement the v2 entities, state transitions, and persistence seams without a major UI change.

**Files changed:** domain entity/value-object modules; repository interfaces and initial implementations; service tests; migration or fixture files as required by the existing persistence approach.

**Acceptance criteria:** User, CareerProfile, Evidence, Preference, Constraint, CareerHypothesis, Career, Job, EvidenceMap, Action, and Outcome can be created and retrieved; only a user confirmation operation can set Evidence to `user_confirmed`; tests cover invalid states and relationships.

## Sprint 2 — Evidence profile

**Goal:** Let a user enter current state, receive evidence candidates, and confirm a trustworthy Career Profile.

**Files changed:** State Entry and Career Profile routes/pages; evidence/profile APIs and services; AI Gateway extraction adapter; evidence-confirmation tests.

**Acceptance criteria:** every candidate evidence item shows original quote and extraction source; the user can edit, confirm, or reject it; unverified/AI-generated content cannot power a trusted claim; current UI remains functional.

## Sprint 3 — Career hypothesis

**Goal:** Support creation and revision of a small, testable Hypothesis Board.

**Files changed:** hypothesis domain/service/API modules; Hypothesis Board page; deterministic validation policies; tests and fixtures.

**Acceptance criteria:** each active hypothesis references a career and supporting evidence or an explicit insufficient-evidence state; unknowns/gaps/falsifiers are visible; hypothesis status supports `exploring`, `strengthened`, `weakened`, `paused`, and `rejected`; the product does not present a free-form AI career ranking or verdict.

## Sprint 4 — Evidence Map

**Goal:** Compare confirmed user evidence with sourced career and job requirements.

**Files changed:** Career/Job repository and source-record modules; Market Reality and Evidence Map pages; comparison service; source and map tests.

**Acceptance criteria:** job records contain source URL and capture date; every map assessment is `supported`, `partial`, `missing`, or `unknown` and traceable to a requirement and evidence or an explicit gap/unknown; `supported` requires confirmed evidence; constraint conflicts are visible.

## Sprint 5 — Resume Translator

**Goal:** Produce a truthful, job-specific resume draft from confirmed evidence.

**Files changed:** Resume Translator page; resume draft domain/service/API modules; AI Gateway writing adapter; validation and regression tests.

**Acceptance criteria:** a target job is selected; each generated bullet links to confirmed Evidence IDs; unsupported statements are rejected or labelled as drafts; user edits do not mutate underlying evidence.

## Sprint 6 — Interview

**Goal:** Add evidence-grounded interview practice and learning capture.

**Files changed:** Interview page and conversation flow; Action/Outcome services; AI Gateway conversation adapter; outcome-to-evidence review flow; tests.

**Acceptance criteria:** questions can be tied to a job requirement and evidence; practice feedback does not invent qualifications; a completed action records an Outcome; any new evidence created from the outcome requires user confirmation.

## Recommended engineering sequence

1. Agree on storage and migration approach for Sprint 1.
2. Write domain and service tests before adding UI routes.
3. Ship every AI operation behind typed AI Gateway contracts and validation.
4. Run a provenance and unsupported-claim regression suite before expanding beyond P0.
