---
name: medical-resume-skill
description: Turn a medical student's real experience into evidence-bound resume bullets for doctoral, clinical research, medical affairs, or health-data paths. Use when the user needs medical resume interviewing, fact confirmation, or target-specific translation; do not use to fabricate or inflate experience.
---

# Medical Resume Skill

Help the user make a medical experience clear, credible, and useful for a chosen target path. Treat confirmed personal facts as the only source of claims. A polished sentence is never a reason to upgrade responsibility or invent an outcome.

## Intake

Ask for the raw experience and one target path. If the target is unclear, offer only these initial paths:

- doctoral / academic application;
- clinical research;
- medical affairs / MSL;
- health AI / medical data.

Extract an **experience fact card** before writing bullets. Keep the following categories distinct:

- research context or disease area;
- study design;
- analytical methods;
- programming/statistical tools;
- wet-lab techniques;
- clinical-research operations and compliance;
- literature/evidence resources;
- personal role and responsibility level;
- deliverables, results, and evidence sources;
- missing or ambiguous information.

For example, R is a tool, MR and Meta-analysis are methods, qPCR is a wet-lab technique, GCP is a compliance framework, CRF is a clinical-research deliverable, and PubMed is an evidence-retrieval resource. Do not group them as one undifferentiated skill list.

## Confirmation before composition

Show the fact card and ask the user to confirm or correct it. Ask no more than three high-value follow-up questions at once. Prefer questions about responsibility, data/material source, method details, measurable results, and deliverables.

Use conservative responsibility language such as “participated”, “supported”, or “completed under supervision” when ownership is uncertain. Do not turn a collaborator into an owner, an assistant into a lead, or a draft into a publication.

Read [evidence rules](references/evidence-rules.md) whenever a claim is ambiguous or strong.

## Compose

After confirmation, write one to three concise bullets tailored to the selected target path. State which confirmed facts each bullet uses, then give a short “what to improve next” note if stronger evidence would improve the bullet.

Read [role packs](references/role-packs.md) before tailoring the output. Translate the same facts by changing emphasis and ordering, not by changing what happened.

## Output format

Use this structure:

```markdown
### Confirmed fact card
- ...

### Resume bullets for <target path>
1. ...

### Evidence and boundaries
- Uses: ...
- Responsibility: ...
- Not claimed: ...

### Optional next questions
1. ...
```

If material facts remain unconfirmed, stop after the fact card and questions. Do not produce a ready-to-submit bullet.
