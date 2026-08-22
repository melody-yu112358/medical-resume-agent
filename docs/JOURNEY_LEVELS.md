# Progressive journey levels

The three depths are checkpoints in one evidence-to-application journey, not
separate products. They share the same profile evidence, career hypotheses and
product boundaries. A user may stop at any checkpoint without being treated as
an incomplete or failed user.

## Level contracts

| Level | User promise | Maximum input | Output | Exit and continuation |
| --- | --- | --- | --- | --- |
| Possibility glimpse | See that medical experience may contain value beyond grades and publications | Three light questions; about three minutes | Up to three capability clues, up to two career worlds and one unanswered question; no score or ranking | Save or leave the glimpse, or continue to evidence collection |
| Career exploration | Turn concrete experience into evidence and compare a small verified career library | Two to three experiences, one focused follow-up at a time and explicit constraints; about fifteen minutes | A user-confirmed evidence profile and no more than three revisable career hypotheses with support, counter-evidence, gaps, sources and one concrete next step | Correct, reject, pause or select one hypothesis |
| Application preparation | Move from a selected direction to a concrete application | One selected direction, one sourced job posting and confirmed resume evidence | A traceable job shortlist, grounded resume revision and JD-specific HR screening practice | Change direction or job, revise, pause or stop |

Application preparation begins only when a user chooses one direction. A career
card describes a role; it must not be presented as a specific job posting.

## Shared state

```text
MedicalProfile
  -> confirmed ProfileEvidence history
  -> current constraints and unknowns

CareerHypothesis
  -> profile evidence references
  -> sourced career claims
  -> counter-evidence, gaps and unknowns
  -> status: proposed, rejected, paused, selected

JobSelection
  -> selected career and stable job_id
  -> sourced JD snapshot and verification date
  -> status, location and explicit constraints

ResumePreparation
  -> original resume evidence and gaps
  -> confirmed supplemental facts
  -> revised wording and change reasons

InterviewSession
  -> selected job and resume references
  -> HR questions and user answers
  -> grounded feedback without hiring predictions
```

Later levels may add confirmed evidence, but they must not silently rewrite the
user's original statements, the stored JD, or historical evidence.

## Transition rules

- The glimpse does not calculate evidence coverage or present a best-fit role.
- A capability clue is explicitly labelled unverified until supported by a
  concrete experience and confirmed by the user.
- Career comparison begins only from confirmed evidence.
- No more than one follow-up question is shown at a time.
- Real-job recommendation begins only after explicit direction selection.
- Resume preparation begins only after a specific versioned `job_id` is chosen.
- Interview questions and feedback stay grounded in that JD and the user's
  confirmed resume evidence.
- Models may not invent job requirements, personal experience, credentials,
  numbers, or hiring probability.
- Staying in medicine, pausing exploration and rejecting every hypothesis are
  valid outcomes.

## Target interface map

```text
/demo/
  -> choose current depth
  -> /demo/journey/glimpse.html
  -> /demo/profile-intake/index.html
  -> job list and job detail
  -> /demo/resume-beta/
  -> HR interview practice

/demo/integration.html
  -> preserved synthetic-profile engineering validation page
```

The shared navigation uses five stable chapters: possibility, evidence,
direction, job and preparation. Dynamic model follow-ups do not display a fixed
question count because their total may vary.

## Acceptance for the journey shell

- The three levels state different time, input and output promises.
- A first-time user is never required to enter application preparation.
- Every level explains how to stop or continue.
- The fifteen-minute entry reuses the implemented grounded profile-intake flow.
- The preparation entry makes direction and job selection prerequisites visible.
- Career directions and specific job postings are visibly distinct.
- The synthetic engineering page remains accessible and separate from the
  user-facing journey.
