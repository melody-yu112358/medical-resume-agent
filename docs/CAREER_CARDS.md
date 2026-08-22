# Career card research guide

## Purpose

Career cards provide the factual input for career hypotheses. They describe
roles and market observations; they do not decide whether a user is suitable
for a role. Every factual claim must be traceable to a source record and remain
open to correction or retirement.

## First scope

The first milestone uses five concrete roles at a comparable level of
granularity:

| Career ID | Canonical name | Career family |
| --- | --- | --- |
| `medical-science-liaison` | Medical Science Liaison (MSL) | Medical affairs |
| `clinical-research-associate` | Clinical Research Associate (CRA) | Clinical research |
| `pharmacovigilance-specialist` | Pharmacovigilance Specialist | Drug safety |
| `medical-writer` | Medical Writer | Medical communications |
| `healthcare-ai-product-manager` | Healthcare AI Product Manager | Healthcare AI |

Healthcare AI is an industry family rather than one job. The first card uses a
product-manager role because it has a searchable job title and a coherent set
of tasks. Algorithm engineering, data science, clinical evaluation, and AI
medical affairs may become separate cards only after the first workflow is
validated.

## Card contents

Each JSON card follows `schemas/career.schema.json` and records:

1. role identity, aliases, and market boundary;
2. daily tasks;
3. education and skill observations;
4. preferred experience;
5. medical capabilities that may transfer;
6. work environment and entry barriers;
7. low-cost validation actions;
8. source metadata, review status, and update date.

## Evidence rules

- The first market boundary is mainland China.
- A job posting is a dated observation, not a universal requirement.
- Every factual claim names one or more `source_ids`.
- Prefer at least three recent sources, including two first-party employer or
  institution sources when available.
- Distinguish quoted, summarized, inferred, and AI-proposed claims.
- Inferred transferability must show the market evidence behind the inference.
- AI-generated prose is never listed as a factual source.
- A new card remains `draft` until another team member checks the claims and
  source links.
- Stale or unavailable sources are labelled or retired rather than silently
  replaced.

## Pilot acceptance

The first card is ready for team review when:

- it parses as JSON and conforms to the career-card contract;
- every referenced source ID exists in the same card;
- support and entry barriers are both visible;
- it does not present sampled requirements as universal market facts;
- its validation actions can be completed without submitting personal data;
- a second team member can mark it `reviewed` or return it for correction.

The detailed source hierarchy, search procedure, freshness rules, and conflict
handling process live in `docs/RESEARCH_METHOD.md`. Technical and product
decisions are recorded chronologically in `docs/BUILD_LOG.md`.
