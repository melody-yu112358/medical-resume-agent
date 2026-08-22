# Unbounded v2 AI System

## Role of AI

AI is a constrained assistant within an evidence-based workspace. It helps users express, organize, understand, and communicate their existing information. It does not become the authority on the user's experience, career choice, or market reality.

## Allowed responsibilities

- **Extraction:** identify candidate Evidence, Preferences, Constraints, requirements, and questions from user-provided or source-linked content.
- **Summarization:** produce concise summaries that preserve uncertainty and source boundaries.
- **Explanation:** explain how evidence relates to a hypothesis, job requirement, gap, or action.
- **Writing assistance:** draft resume bullets, outreach notes, reflections, and interview practice material from selected confirmed evidence.
- **Conversation:** guide the user through clarification, confirmation, and reflection.

## Forbidden responsibilities

- Inventing experience, credentials, outcomes, skills, metrics, or quotations.
- Modifying evidence, its original quote, or its extraction source.
- Ranking careers freely or declaring a single best career without deterministic, user-visible criteria.
- Modifying deterministic career scores, ordering, or comparison results.
- Generating unsupported market facts, current job availability, salaries, hiring conditions, or requirements.
- Predicting employment success or presenting a probability of getting hired.
- Setting an evidence item to `user_confirmed`, removing a material unknown, or completing an action without user review.

## Output states

Every persisted AI-assisted item must expose one of the following states:

| State | Meaning | Consequential use |
| --- | --- | --- |
| `draft` | Initial generated or user-started content that has not been reviewed | Display and edit only |
| `unverified` | Extracted/imported content with a source but awaiting validation | May inform questions; cannot support a conclusion |
| `user_confirmed` | Reviewed and accepted by the user | May be used as trusted evidence subject to domain validation |

`unknown` is not an AI output state. It is a domain conclusion that material information is missing. The AI should surface it instead of guessing.

## Input and provenance requirements

- Give the model only the minimum context needed for the task.
- Label input origin: user entry, uploaded document, confirmed evidence, career source, job source, or prior draft.
- Preserve the exact original quote for candidate Evidence and include its source locator.
- Require structured output with item type, source references, uncertainty flags, and rationale.
- Do not present model confidence as truth or use it as a career ranking score.

## Required safeguards by use case

### Evidence extraction

The model returns candidate claims linked to text spans. The service creates `draft` or `unverified` records only. A user confirmation command is required before trusted use.

### Career hypothesis assistance

The model may formulate a hypothesis statement and list supporting evidence, gaps, and unknowns. It must not output a verdict. The system must show evidence links and permit the user to reject the framing.

### Market explanation

The model may summarize supplied Career or Job records. It must not supplement missing facts from model memory. If the source does not establish a claim, the output must say `unknown` or request a source.

### Resume Translator

The model receives only selected `user_confirmed` Evidence and the target job. Each draft bullet must return supporting evidence IDs. Unsupported claims are rejected by the service before display as a candidate bullet.

### Interview and conversation

The model can ask questions, simulate interviews, and offer phrasing feedback. It must separate practice feedback from factual assertions about the user's suitability or market outcomes.

## Evaluation and monitoring

Before release, evaluate representative tasks for:

- evidence quote and source retention;
- false experience creation (must be zero-tolerance);
- correct refusal to assert unsupported market facts;
- visibility of unknowns and gaps;
- coverage of source-linked evidence in resume drafts;
- user ability to correct or reject output.

Log prompt version, model version, structured output, validation result, and user disposition. Do not retain unnecessary sensitive user content in evaluation data.
