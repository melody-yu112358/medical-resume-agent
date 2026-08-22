# Unbounded v2 Technical Design

## Scope

This document aligns future technical work with the v2 domain model. It does not require an immediate rewrite of the current demo.

## Frontend

### Current stack

- Flask backend
- HTML/CSS/JavaScript demo pages

Existing pages remain intact during the documentation phase. New implementation work should add flows incrementally and avoid coupling UI state directly to LLM responses.

### Future page structure

| Page | Primary responsibility |
| --- | --- |
| State Entry | Capture current situation, transition intent, and constraints without forcing conclusions |
| Career Profile | Review and confirm Evidence, Preferences, and Constraints with their sources |
| Hypothesis Board | Create, compare, and revise testable CareerHypotheses |
| Market Reality | Present source-linked Career and Job information with dates and uncertainty |
| Evidence Map | Compare verified user evidence to role requirements, gaps, and unknowns |
| Action Workspace | Create experiments, track outcomes, and convert reviewed outcomes into new evidence |
| Resume Translator | Produce a job-targeted resume using only confirmed evidence |

### Client responsibilities

- Clearly render `draft`, `unverified`, `user_confirmed`, and `unknown` states.
- Require a visible user confirmation action before evidence becomes trusted.
- Preserve source links, original quotes, and model rationale in drill-down views.
- Send domain commands to APIs; do not embed career decision rules or provenance logic in page scripts.

## Backend architecture

The Flask application should evolve by separating responsibilities while preserving the existing entry points.

```text
Frontend pages
    ↓
API Layer
    ↓
Service Layer
    ↓
Domain Layer
    ↓
Repository Layer

Service Layer ↔ AI Gateway
```

### API Layer

Provides HTTP routes, request validation, authentication context, response serialization, and error mapping. It must not contain domain decisions or direct model prompts.

### Service Layer

Coordinates use cases such as extracting evidence candidates, confirming evidence, creating hypotheses, generating an Evidence Map, recording an outcome, and drafting a resume. It owns transactions and authorization checks.

### Domain Layer

Contains entities, value objects, validation policies, and deterministic rules defined in `DOMAIN_MODEL_V2.md`. It decides, for example, whether an EvidenceMap item is allowed to be `supported`.

### Repository Layer

Persists and retrieves domain entities, source records, confirmation history, and audit data. Repository methods expose domain concepts rather than page-specific data shapes.

The MVP may preserve the current JSON-backed approach behind repository interfaces. PostgreSQL plus search is a future storage direction, not a Sprint 0 dependency.

### AI Gateway

Is the only adapter that calls language models. It accepts typed inputs and returns typed drafts with provenance, prompt/version metadata, and failures. It cannot write `user_confirmed` evidence, change domain states, or bypass service-layer validation.

## Core use-case boundaries

| Use case | Input | Output | Required guardrail |
| --- | --- | --- | --- |
| Extract evidence candidates | User text or document | Draft candidate list | Preserve source text and extraction source |
| Confirm evidence | User edits and confirmation | Trusted Evidence | User-only state transition to `user_confirmed` |
| Create hypothesis | Career + profile context | CareerHypothesis | No verdict or free-form ranking |
| Build Evidence Map | Job/Career requirements + confirmed evidence | Supported, partial, missing, or unknown mappings | Support requires confirmed evidence |
| Draft resume | Job + selected confirmed evidence | Draft resume content | Every claim must cite supporting evidence IDs |

## Data and audit design

- Store original user quotes separately from normalized claims.
- Keep external source URL, publisher where available, and capture timestamp for Career and Job content.
- Use append-only confirmation/audit events for changes in verification state.
- Treat model outputs as ephemeral drafts unless persisted with their source, model version, and user review outcome.
- Use opaque IDs in APIs; never expose another user's content through predictable identifiers.

## Incremental implementation guidance

1. Add domain models and repositories before changing visual flows.
2. Introduce APIs around a single user profile and evidence confirmation flow.
3. Put model integrations behind the AI Gateway before using them for any feature.
4. Add Evidence Map and Resume Translator only after trusted evidence and source-linked job data exist.
