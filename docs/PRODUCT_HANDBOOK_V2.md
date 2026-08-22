# Unbounded v2 Product Handbook

**Version:** v2.0 Product Foundation

**Status:** Draft for team alignment

**Owner:** Product Team

**Purpose:** Define the product vision, user journey, MVP boundary, and system principles for Unbounded v2.

## 1. Product vision

Unbounded (未界) is an evidence-based career transition workspace for medical professionals. Its core mission is to reduce uncertainty during a career transition. It helps a user turn lived experience into verified career evidence, form testable career hypotheses, compare those hypotheses with market reality, take practical action, and learn from the outcome.

The product loop is:

> Evidence → Hypothesis → Reality → Action → New Evidence

Unbounded is not a career recommendation engine, personality test, resume generator, or recruitment platform. It does not decide a user's future. It makes the transition process legible, grounded, and iterative.

## 2. User problem

Medical professionals often have substantial experience but lack a structured way to translate it into cross-industry capability. They face three connected problems:

1. Their experience is stored as scattered memories, not reusable and verifiable evidence.
2. Possible careers feel either too numerous or prematurely certain; users need hypotheses, not verdicts.
3. Job descriptions, market signals, resumes, and interviews are disconnected from a user's actual evidence and constraints.

The workspace closes this gap by retaining the user's source statements, making uncertainty visible, and connecting every suggested action to a learning objective.

## 3. Target users

### Primary users

- Medical students, residents, clinicians, researchers, and healthcare operations professionals considering a transition outside a conventional clinical path.
- Professionals with 0–8 years of post-graduation experience who need to explore without erasing their medical identity or making an irreversible commitment.

### Secondary users

- Medical professionals returning after a career break or shifting between healthcare-adjacent roles.
- Career advisers or mentors who need a shared, evidence-grounded view of a user's transition work.

## 4. Product principles

### Evidence First

Claims about a user begin with an attributable source: the user's words, an uploaded record, or a clearly identified external source. LLM output is never trusted evidence by itself.

### Hypothesis Not Verdict

A career direction is a testable proposition with supporting evidence, objections, gaps, and unknowns. The product does not label a career as the user's single “best” answer.

### Reality Grounded

Career and job information must distinguish sourced fact, interpretation, and unknown. Recommendations must account for actual role requirements and user constraints.

### Action Creates Evidence

The useful next step is an experiment that can produce a concrete outcome: a conversation, portfolio artifact, application response, or skill demonstration.

### Unknown Is Information

Missing information is explicit, not silently filled by AI. Unknowns become questions, research tasks, or experiments.

## 5. Product architecture

### Career Memory Layer

- **Evidence** — verified claims grounded in a source statement or record.
- **Preference** — what the user is drawn to, avoids, or values at work.
- **Constraint** — non-negotiable or bounded conditions such as location, time, income, licensing, or caregiving.

### Reasoning Layer

- **Career Hypothesis** — a direction to investigate, with rationale and falsifiers.
- **Unknown / Unknown Ledger** — a visible record of material questions that lack sufficient evidence.
- **Gap** — a difference between the user's current evidence and a career or job requirement.

### Reality Layer

- **Career information** — sourced understanding of a career's work, pathways, and conditions.
- **Job information** — a dated, source-linked representation of a specific opportunity.
- **Evidence Map** — the traceable alignment between user evidence, role requirements, gaps, and uncertainties.

### Action Layer

- **Experiment** — a bounded activity designed to learn or validate.
- **Resume** — a job-targeted presentation of only supported evidence.
- **Interview** — practice and reflection tied to evidence and job requirements.

## 6. MVP boundary

| Priority | Included capability |
| --- | --- |
| P0 | User state entry; evidence extraction and confirmation; career hypothesis; job reality; Evidence Map; Resume Translator |
| P1 | Interview; Transition Companion; Work Preference Exploration |
| P2 | Community; auto application; salary prediction |

P0 proves the full learning loop. A user can enter their current state, confirm evidence, investigate a plausible career against real jobs, see what is supported or unknown, and create a truthful job-targeted resume.

## 7. Product decisions and guardrails

- A user can edit, confirm, reject, or delete any personal claim before it becomes trusted evidence.
- The product records evidence provenance and verification state throughout the workflow.
- Career hypotheses are displayed side-by-side without an unconstrained AI ranking.
- A hypothesis can move through `exploring`, `strengthened`, `weakened`, `paused`, and `rejected` as new evidence arrives.
- External market content is dated, sourced, and permitted to remain incomplete.
- Resumes and interview materials may improve clarity but must not add accomplishments, skills, metrics, credentials, or market facts not supported by evidence.

## 8. MVP success measures

MVP success is not defined by whether the product gets a user hired. The first release should demonstrate that a user can:

1. identify and explain their confirmed capability evidence;
2. understand at least one career hypothesis without treating it as a verdict;
3. identify a material gap or unknown against market reality; and
4. complete a concrete next action that produces learning or new evidence.

### North-star metric: Evidence Progress

Evidence Progress measures whether a user is reducing transition uncertainty through verified learning. Initial signals include:

- newly user-confirmed Evidence items;
- material Unknowns investigated or resolved;
- Actions completed with recorded Outcomes; and
- CareerHypotheses strengthened, weakened, paused, or rejected using new evidence.

These are learning signals, not employability or personal-worth scores. Counts must not reward low-quality evidence creation or pressure users to generate activity without a clear learning purpose.

## 9. Documentation governance

These six v2 foundation documents are the product baseline for new v2 work:

- `PRODUCT_HANDBOOK_V2.md`
- `USER_JOURNEY_V2.md`
- `DOMAIN_MODEL_V2.md`
- `TECHNICAL_DESIGN_V2.md`
- `AI_SYSTEM_V2.md`
- `MVP_EXECUTION_PLAN_V2.md`

Existing documents such as `PRODUCT.md`, `ARCHITECTURE.md`, `WORKFLOW.md`, and `JOURNEY_LEVELS.md` remain valid records of the current implementation and earlier decisions. They are not deleted or silently rewritten in Sprint 0. When a future engineering task encounters a conflict, it must identify the conflict explicitly and either align the implementation with the v2 baseline or record a deliberate exception. Legacy documents may be migrated or marked superseded only through a separate reviewed change.
