# MVP workflow

The first milestone is one progressive workflow, not three separate products.
A user may stop after a possibility glimpse, continue into career exploration,
or continue into job-specific application preparation.

```text
consent and scope
  -> collect a small amount of experience, uncertainty, and constraints
  -> identify initial capability clues and unanswered questions
  -> checkpoint: save a possibility glimpse and stop, or continue

career exploration
  -> collect fuller profile evidence
  -> identify missing critical information
  -> ask one focused follow-up question
  -> retrieve verified career records
  -> apply hard constraints
  -> compare transferable skills and gaps
  -> produce at most three hypotheses
  -> show support, counter-evidence, uncertainty, and sources
  -> checkpoint: correct, reject, pause, or select a direction

application preparation
  -> retrieve sourced real-job postings for the selected direction
  -> filter by explicit constraints and show status and freshness
  -> select one versioned job_id
  -> compare confirmed resume evidence with the stored JD
  -> ask for missing facts without inventing experience
  -> produce a traceable resume revision and change explanation
  -> run an HR screening simulation grounded in the JD and resume
  -> checkpoint: revise, change job, pause, or stop
```

## Capability-evidence contract

A degree, publication, project, or clinical placement is not capability
evidence by itself. A usable evidence item should record, when available:

```text
context
  -> task or responsibility
  -> action performed by the user
  -> result
  -> verifiable artifact or reference
  -> capability supported
  -> evidence strength and uncertainty
```

Evidence strength describes how strongly the available information supports a
specific capability claim. It does not score the user's worth or overall
potential.

## Decision rules

- The model may extract and explain evidence; it may not invent evidence.
- Deterministic code applies hard constraints and calculates any numeric score.
- A score is never presented without its components and limitations.
- When career data is missing or stale, the system says so.
- One follow-up question is asked at a time.
- Every inferred capability is shown to the user for correction.
- A user may leave at any checkpoint without being treated as a failed journey.
- User rejection updates the working hypothesis, not the historical evidence.
- Job facts come from a stored, versioned source record; a career card may not
  masquerade as a specific JD.
- Resume wording and interview feedback may not add unconfirmed experience,
  numbers, credentials, or hiring predictions.

## Proposed DSH boundary

DeepSeek Harness may provide the agent loop, sessions, tools, approvals, and
initial Web UI. Domain behavior should remain portable behind tools such as:

- `update_medical_profile`
- `search_career_evidence`
- `compare_career_paths`
- `search_job_postings`
- `prepare_targeted_resume`
- `conduct_hr_interview`

No DSH dependency is added until a small technical spike confirms that its
preview API is sufficiently stable for this workflow.
