# First-milestone acceptance criteria

## Correctness

- All career facts shown to a user map to a stored source record.
- All personal evidence in a recommendation maps to the user's supplied data.
- Each capability claim identifies the experience that supports it and whether
  the claim is user-provided, inferred, or still unverified.
- Hard constraints exclude incompatible paths before ranking.
- Unknown, conflicting, and stale information is labelled.
- Each hypothesis includes at least one counter-evidence or unresolved item
  when one exists; the system does not hide it to improve apparent fit.
- The output makes no employment, salary, or guaranteed-fit promise.
- Resume output and interview feedback do not invent experience, credentials,
  numbers, job facts, or hiring predictions.

## Usability

- A user can complete intake without answering more than one question at once.
- A user can save a possibility glimpse and leave before completing the full
  exploration flow.
- The result contains no more than three career hypotheses.
- Each hypothesis includes support, counter-evidence, gaps, and a concrete next step.
- A user can identify which of their experiences led to each hypothesis.
- A user can correct the profile and reject, pause, or select a hypothesis.
- A selected direction leads to sourced real-job postings before resume work.
- Selecting a `job_id` starts resume diagnosis without requiring the user to
  paste the JD again.
- The experience does not frame staying in medicine, pausing exploration, or
  declining application preparation as failure.

## Application-preparation loop

- Every job shows company, location, status, source, and last verification date.
- Resume diagnosis separates original evidence, gaps, follow-up questions, and
  generated wording.
- Resume revisions show the original text, revised text, and reason for change.
- HR questions are grounded in the selected JD and confirmed resume evidence.
- Interview feedback points to the user's answer and the relevant job
  requirement without estimating hiring probability.
- The user can change direction or job and can remove transient personal data.

## Initial evaluation gate

Test with at least three consenting users using data kept outside Git. The first
milestone passes when:

- at least two users identify one hypothesis worth testing and can explain the
  evidence and uncertainty behind it;
- at least one user selects a sourced job, completes a grounded resume revision,
  and finishes one HR screening simulation;
- the participant can explain which JD requirements and personal evidence
  produced the resume and interview feedback;
- participants can correct or reject a system inference without losing their
  original evidence.

Visual polish and additional career coverage are optional after correctness and
usability pass.
