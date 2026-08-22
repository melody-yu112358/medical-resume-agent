# Unbounded v2 Domain Model

## Model rules

- Every entity has an immutable `id`, `created_at`, `updated_at`, and `created_by`.
- User-visible claims retain provenance. AI-generated text is an assistive draft until user confirmation.
- `verification_status` values are `draft`, `unverified`, and `user_confirmed`. Only `user_confirmed` evidence may be used as trusted support in an Evidence Map or Resume.
- Relationships should use IDs; audit history belongs in the repository layer rather than overwriting source content.

## User

**Purpose:** Owns data, consent, and access to a transition workspace.

**Fields:** `id`, `email`, `display_name`, `locale`, `consent_version`, `created_at`, `updated_at`.

**Relationships:** has many CareerProfiles, CareerHypotheses, Actions, and Outcomes; owns all personal Evidence, Preferences, and Constraints through a CareerProfile.

**Validation rules:** email is unique and normalized; consent is required before AI processing or external data import; a user can access only their own records unless explicit sharing is added later.

## CareerProfile

**Purpose:** Stores the user's current career memory and transition context.

**Fields:** `id`, `user_id`, `headline`, `current_state`, `transition_goal`, `profile_status`, `version`.

**Relationships:** belongs to one User; has many Evidence, Preferences, Constraints, and CareerHypotheses.

**Validation rules:** exactly one active profile per user for MVP; `current_state` is user-authored or user-confirmed; profile version increments when confirmed memory changes.

## Evidence

**Purpose:** Represents a traceable, scoped claim about the user's experience, ability, education, credential, or result.

**Fields:** `id`, `career_profile_id`, `claim`, `evidence_type`, `context`, `task`, `action`, `result`, `capability`, `original_quote`, `extraction_source`, `source_locator`, `source_date`, `verification_status`, `confirmed_at`, `confidence_note`, `tags`.

**Relationships:** belongs to one CareerProfile; can support or challenge many CareerHypotheses; links to many EvidenceMap entries and Resume claim links; may be created from an Outcome after user confirmation.

**Validation rules:** `original_quote` is required and immutable after creation; `extraction_source` is required (`user_entry`, `conversation`, `document`, `manual`, or `outcome`); `verification_status` must be one of the model states; only the user can set `user_confirmed`; LLM-generated content cannot directly become trusted evidence; claims must retain their source locator when a source exists.

## Preference

**Purpose:** Captures a tentative work preference without presenting it as a fact about aptitude or fit.

**Fields:** `id`, `career_profile_id`, `statement`, `dimension` (for example work style, subject matter, environment), `strength`, `original_quote`, `verification_status`.

**Relationships:** belongs to one CareerProfile; can influence many CareerHypotheses and Actions.

**Validation rules:** statement must preserve a user source; strength is an ordinal user-selected signal, not an AI score; preferences never override a hard Constraint.

## Constraint

**Purpose:** Records conditions that limit or shape viable transition options.

**Fields:** `id`, `career_profile_id`, `constraint_type`, `description`, `priority`, `hardness`, `original_quote`, `verification_status`, `effective_from`, `effective_until`.

**Relationships:** belongs to one CareerProfile; may challenge CareerHypotheses, Jobs, and Actions.

**Validation rules:** `hardness` is `hard` or `soft`; hard constraints must be considered in comparison but do not automatically delete a hypothesis; time-bounded constraints require both dates when an end date is known.

## CareerHypothesis

**Purpose:** Represents a career direction worth testing, not a recommendation or outcome prediction.

**Fields:** `id`, `career_profile_id`, `career_id`, `statement`, `status`, `rationale`, `falsifiers`, `unknown_ids`, `supporting_evidence_ids`, `created_at`.

**Relationships:** belongs to one CareerProfile; references one Career; links to Evidence, EvidenceMaps, Actions, and Outcomes.

**Validation rules:** must link to at least one Career; `status` is `exploring`, `strengthened`, `weakened`, `paused`, or `rejected`; active hypotheses must include at least one supporting confirmed Evidence or an explicit “insufficient evidence” state; must show at least one unknown, gap, or falsifier; no unconstrained AI-generated rank is stored as the hypothesis conclusion.

## Career

**Purpose:** Defines a reusable, sourced description of a career direction.

**Fields:** `id`, `name`, `summary`, `work_activities`, `typical_requirements`, `pathways`, `source_records`, `last_reviewed_at`, `status`.

**Relationships:** has many CareerHypotheses and Jobs; supplies requirements used by EvidenceMaps.

**Validation rules:** sourced assertions require a source record and capture date; general career information must not be represented as a current job opening; stale or incomplete records are labelled accordingly.

## Job

**Purpose:** Stores a dated representation of a specific market opportunity.

**Fields:** `id`, `career_id`, `title`, `employer`, `location`, `work_mode`, `employment_type`, `requirements`, `responsibilities`, `source_url`, `source_published_at`, `captured_at`, `job_status`.

**Relationships:** belongs to one Career; has many EvidenceMaps and resume targets.

**Validation rules:** `source_url` and `captured_at` are required; requirements must distinguish verbatim source text from normalized interpretation; expired or removed jobs remain historical records and cannot be labelled active without revalidation.

## EvidenceMap

**Purpose:** Explains how user evidence relates to a selected Career or Job requirement.

**Fields:** `id`, `career_profile_id`, `career_hypothesis_id`, `target_type`, `target_id`, `requirement_text`, `assessment` (`supported`, `partial`, `missing`, `unknown`), `evidence_ids`, `rationale`, `constraint_conflict`, `verification_status`.

**Relationships:** belongs to one CareerProfile and one CareerHypothesis; points to one Career or Job; references many Evidence items; generates candidate Actions.

**Validation rules:** must have one target and one requirement; `supported`/`partial` requires at least one `user_confirmed` Evidence item; `missing`, `unknown`, and constraint conflicts cannot be silently converted into support by AI; rationale must distinguish quoted evidence from interpretation.

## Action

**Purpose:** Defines a bounded experiment or preparation task that can create learning.

**Fields:** `id`, `career_profile_id`, `career_hypothesis_id`, `evidence_map_id`, `action_type`, `title`, `learning_question`, `completion_criteria`, `status`, `due_at`, `owner_id`.

**Relationships:** belongs to a CareerProfile; may link to a CareerHypothesis and EvidenceMap; has many Outcomes.

**Validation rules:** action must have a learning question and completion criterion; an action can be completed only with an Outcome or an explicit cancellation reason; actions do not change hypothesis status without user review.

## Outcome

**Purpose:** Records what happened after an action and what the user learned.

**Fields:** `id`, `action_id`, `result`, `reflection`, `source_artifacts`, `occurred_at`, `verification_status`, `hypothesis_effect` (`supports`, `weakens`, `neutral`, `unknown`).

**Relationships:** belongs to one Action; can produce candidate Evidence and update a CareerHypothesis after user review.

**Validation rules:** must link to a completed Action; `result` retains the user's wording or artifact reference; an Outcome is not Evidence until a separate Evidence record is created and user-confirmed; `hypothesis_effect` is a user-reviewed interpretation, not an automatic AI conclusion.
