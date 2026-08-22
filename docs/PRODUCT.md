# Product scope

## Product thesis

Medical education rewards grades, degrees, publications, research projects,
and clinical progression. The wider career market evaluates a different set of
signals: problems solved, responsibilities taken, transferable capabilities,
and evidence that those capabilities were used in practice.

Medical Career Agent helps users translate medical experience into capability
evidence that can be understood and tested in the career market. It does not
decide whether someone should leave medicine. It helps them form career
hypotheses, examine counter-evidence, and gain better evidence through
low-cost action.

## Intended user

A medical student, postgraduate medical trainee, resident, or recent medical
graduate who is considering a non-traditional career path but does not yet have
enough self-knowledge or reliable market information to choose a direction.

The first milestone does not serve medical-school applicants, senior-physician
executive search, generic career assessment for all professions, or mental
health diagnosis and treatment.

## Long-term vision

The long-term product is an ongoing career-transition workspace. A user's
profile develops through career exploration, small work samples, learning,
applications, interviews, offers, and early role experience. The workspace may
eventually support:

- a verified career and industry library;
- a revisable capability-evidence profile;
- career comparison and skill-gap planning;
- application materials and interview practice;
- application and feedback tracking;
- offer comparison and early-role adaptation.

This product map describes direction, not the scope of the first release.

## Progressive experience

Users differ in both readiness and available effort. The first experience must
allow three depths without forcing everyone through the deepest workflow:

1. **Possibility glimpse**: three to five light questions produce capability
   clues, one or more career worlds worth noticing, unanswered questions, and
   explicit permission to stop for now.
2. **Career exploration**: a more complete evidence profile produces no more
   than three career hypotheses with explanations and counter-evidence.
3. **Application preparation**: a user selects a direction, compares sourced
   real job postings, prepares a grounded resume for one JD, and practises an
   HR screening interview.

For the first milestone these are not three independent products. The
possibility glimpse is an early exit from the main exploration flow, and the
application-preparation flow begins only after the user explicitly chooses a
career direction and a specific job posting.

The time, input, output, transition and shared-state contracts for these three
depths are defined in `docs/JOURNEY_LEVELS.md`.

## First deliverable

The first milestone validates one complete loop:

```text
profile evidence
  -> career hypotheses
  -> sourced real-job shortlist
  -> selected JD
  -> grounded resume revision
  -> HR screening practice and feedback
```

Given a structured profile and a small verified career library, the product
returns no more than three career hypotheses. Each hypothesis contains:

1. user evidence supporting the hypothesis;
2. constraints or evidence against it;
3. missing or uncertain information;
4. verified career facts with sources;
5. a concrete next step into sourced job postings.

After the user selects one direction, the product shows traceable real-job
postings rather than treating a career card as a JD. A selected `job_id` drives
deterministic resume diagnosis, bounded resume wording, and HR interview
practice. The model may not alter the stored job requirements, invent user
experience, or estimate hiring probability.

## Product principles

1. **Translate achievements into evidence, not worth.** Degrees, publications,
   and projects may contain evidence of research, judgment, communication,
   collaboration, or execution. They do not automatically prove those
   capabilities.
2. **Recommendations are hypotheses, not verdicts.** Users may correct, reject,
   pause, or overturn every proposed direction.
3. **Support and counter-evidence carry equal weight.** A hypothesis must show
   why it is worth exploring, what may not fit, and what remains unknown.
4. **Preparation must stay grounded.** Real postings, targeted resume work, and
   interview practice must remain traceable to the JD and the user's confirmed
   evidence.
5. **Acknowledge uncertainty without exploiting anxiety.** The product does not
   frame leaving medicine as the only solution, describe staying as failure,
   or promise employment, income, or success.

## Initial career scope

- Medical Science Liaison (MSL)
- Clinical Research Associate (CRA)
- Pharmacovigilance Specialist
- Medical Writer
- Healthcare AI Product Manager

These entries are scope placeholders, not verified career claims. Each first-
milestone card describes a concrete role that a user can search for and test.
Broader labels such as medical affairs, clinical research, and healthcare AI
remain career families rather than separate cards.

## Out of scope for the first milestone

- automated job applications;
- technical interview, offer, and onboarding workflows as complete products;
- promises of employment, salary, or suitability;
- diagnosis or treatment of mental health conditions;
- autonomous modification of recommendation rules from user feedback;
- broad scraping of restricted recruitment platforms;
- production migration of PAEG;
- production dependency on DeepSeek Harness while it remains in preview.
