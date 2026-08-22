# Unbounded v2 User Journey

## Journey overview

The v2 journey turns an ambiguous transition question into a sequence of evidence-grounded decisions.

| Stage | User intent | Product outcome | Primary artifact |
| --- | --- | --- | --- |
| State Entry | “Where am I now?” | A clear transition context and immediate constraints | Current State |
| Career Profile | “What can I credibly claim?” | Confirmed evidence, preferences, and constraints | Career Profile |
| Hypothesis Board | “What could I explore?” | 1–3 testable career hypotheses | Hypothesis Board |
| Market Reality | “What is actually required?” | Sourced career and job understanding | Career / Job Records |
| Evidence Map | “Where do I fit and what is missing?” | Traceable support, gaps, and unknowns | Evidence Map |
| Action Workspace | “What should I learn next?” | Bounded experiments with outcomes | Action Plan |
| Resume Translator | “How do I present my evidence?” | A truthful, job-targeted resume draft | Resume Draft |

## 1. State Entry

The user starts with a plain-language description of their situation: current role, transition trigger, urgency, possible directions, and known constraints. They may say “I want to leave clinical work but do not know where to begin.” The entry can also offer recognizable states:

- I do not know what I can do outside medicine.
- I have several directions but do not know how to choose.
- I know the direction but do not know whether I am ready.
- I have found a job and want to prepare an application.
- I am unsure whether to leave my current path at all.

The product responds by structuring—not judging—the entry. It captures known facts and marks everything else as unknown.

**Exit criteria:** the user has reviewed a concise Current State containing at least one goal, one constraint or explicit “not yet known”, and their source entry.

## 2. Career Profile

The user adds experiences through conversation, forms, or records. AI may extract candidate evidence such as “coordinated a multi-disciplinary study,” but each candidate remains a draft until the user confirms it.

The profile separates three kinds of memory:

- evidence: supported statements about work, education, skills, and outcomes;
- preferences: exploratory signals about desired work;
- constraints: conditions that shape feasible choices.

**Exit criteria:** the user has confirmed, edited, or rejected extracted items. The profile shows original quotes and sources for confirmed evidence.

## 3. Hypothesis Board

The user creates or reviews a small set of career hypotheses. Each hypothesis states why it may fit, which evidence supports it, what could disprove it, and what is unknown. It is not a score or a final recommendation. As the user learns, its status can change among `exploring`, `strengthened`, `weakened`, `paused`, and `rejected`.

Example: “Clinical research operations may be a viable direction because I have protocol coordination and stakeholder evidence; I still need to learn whether its travel and location requirements fit my constraints.”

**Exit criteria:** each active hypothesis links to at least one evidence item and has at least one unknown, gap, or falsifying condition.

## 4. Market Reality

The user explores a sourced career summary and real job records. The interface distinguishes job-specific requirements from general career descriptions and records the source URL and capture date.

The user can save a job as a comparison target without applying through Unbounded.

**Exit criteria:** a selected hypothesis has a career record or at least one job record with identifiable sources; unsupported market claims are marked unknown rather than inferred.

## 5. Evidence Map

The Evidence Map makes the comparison visible. It connects each role requirement to:

- supporting confirmed evidence;
- contradicting evidence or constraints;
- a gap requiring development or clearer proof; or
- an unknown requiring research.

The user can challenge a link and revise the underlying evidence or mapping. The map does not calculate an authoritative career verdict.

**Exit criteria:** the user can identify a next question or action for each material gap/unknown, and can trace all support back to an evidence source.

## 6. Action Workspace

The user chooses a small experiment rather than an abstract “next step.” Actions may collect missing information, explore the market, create evidence, or prepare an application. Examples include an informational interview, analysis of five job posts, a portfolio artifact, or a 90–120 minute product-analysis exercise that produces a one-page requirements document.

Afterward, the user records the outcome. The outcome can support, weaken, or leave unchanged a career hypothesis. It becomes new evidence only after review and verification.

**Exit criteria:** an action has a learning question, completion condition, and recorded outcome or an explicit incomplete state.

## 7. Resume Translator

For a chosen job, the user selects confirmed evidence to translate into employer-readable wording. AI can summarize and draft, but the user approves each claim. The resume clearly remains a presentation of existing evidence, not a source of new evidence.

**Exit criteria:** every resume bullet links to one or more confirmed evidence items and the target job is identified.

## Cross-cutting states

- **Draft:** created by the user or AI; not trusted for consequential reasoning.
- **Unverified:** extracted or imported information awaiting user review or source validation.
- **User confirmed:** reviewed and accepted by the user; eligible for reasoning and resume translation.
- **Unknown:** material information is absent; the product should create a question rather than a claim.
