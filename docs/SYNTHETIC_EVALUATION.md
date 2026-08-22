# Synthetic profile evaluation

## Purpose

Synthetic profiles let the team test recommendation behavior before collecting
real participant data. They are deliberately fictional and may be committed to
Git. They do not describe a real student, a typical student, or a successful
transition story.

The first evaluation set contains three contrasting cases:

1. a clinical communicator with evidence-translation experience;
2. a research builder with small user-research and prototyping experience;
3. a safety coordinator with documentation and process evidence.

The variation is designed to test evidence handling and constraints, not to
create personality types.

## How to interpret expected hypotheses

The records in `data/evaluations/synthetic-profile-cases.cn.json` are evaluation
boundaries, not answer keys. A listed career is a reasonable hypothesis to
explore if the system cites the specified personal evidence, shows the stated
counter-evidence and unknowns, and proposes a low-cost test.

The system is not required to give every listed hypothesis or preserve their
file order. It must return no more than three. A different hypothesis is
acceptable only when its personal evidence and market claims are traceable and
its conflicts are visible.

The evaluation must never treat a hypothesis as:

- a claim that the person is naturally suited to the career;
- a prediction of employment, salary, or success;
- permission to ignore a location, travel, time, or other hard constraint;
- evidence for a capability that the profile does not contain.

## Review procedure

For each case:

1. load the synthetic profile and verified career cards;
2. apply hard constraints before comparison;
3. produce at most three career hypotheses;
4. map every supporting statement to an `evidence_id`;
5. include counter-evidence and unresolved questions;
6. use career-card sources for market claims;
7. propose one feasible action that creates new evidence;
8. check the case's `forbidden_conclusions`.

The first three failure classes to track are:

- **invented support**: the output claims a capability not present in the
  profile;
- **hidden conflict**: a hard constraint or material gap is omitted;
- **verdict language**: a revisable hypothesis is presented as a fixed fit or
  destiny.

## Privacy boundary

Only synthetic cases belong in this directory. Real resumes, names, contact
details, interview transcripts, and identifiable health information must stay
outside Git. Consenting-user tests should use an approved storage process and
feed only anonymized aggregate findings back into the repository.
