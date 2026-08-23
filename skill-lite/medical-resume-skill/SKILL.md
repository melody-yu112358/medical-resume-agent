---
name: medical-resume-skill
description: Turn confirmed medical experience into target-specific, evidence-bound resume bullets and a printable HTML resume. Use for medical students or early-career researchers preparing academic applications, clinical research, medical affairs, or health-data resumes; never use it to invent or inflate experience.
---

# Medical Resume Skill

Help the user translate real medical experience into concise, credible material for a chosen direction. This is an experience translator, not a text inflator: a polished sentence is never a reason to upgrade responsibility, invent an outcome, or attach a skill the user did not use.

Choose one working mode before asking detailed questions:

- **Build from material** — turn fragments, notes, or one experience into a confirmed fact card and resume bullets.
- **Polish an existing resume** — let the user select one to three existing entries; preserve their content and improve only the selected entries.
- **Deliver a resume** — after content is accepted, assemble it into a printable HTML resume. Read [HTML delivery](references/html-delivery.md).

## Non-negotiable boundary

Use only confirmed personal facts. Missing information becomes a question, a `[待补]` item, or a conservative sentence; it must not become a stronger claim. Never write visible internal evidence IDs into a candidate-facing resume.

## Intake

Ask for the raw experience or the selected existing entry, then one target path. If the target is unclear, offer only these initial paths:

- academic progression / research application;
- clinical research / hospital research;
- medical affairs / MSL;
- health data / digital health.

For an existing resume, do not re-interview the entire person. First ask which one to three entries need work, the intended direction, and whether the user wants a light edit or a fuller fact check.

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

For example, R is a programming/statistical tool, MR and Meta-analysis are analytical methods, qPCR is a wet-lab technique, GCP is a compliance framework, CRF is a clinical-research document or workflow artifact, and PubMed is an evidence-retrieval resource. Do not group them as one undifferentiated skill list. Read the [capability taxonomy](references/capability-taxonomy.md) when extracting or presenting capabilities.

## Confirmation before composition

Show the fact card and ask the user to confirm or correct it. Ask no more than three high-value follow-up questions at once. Prefer questions about responsibility, data/material source, method details, measurable results, and deliverables.

Use conservative responsibility language such as “participated”, “supported”, or “completed under supervision” when ownership is uncertain. Do not turn a collaborator into an owner, an assistant into a lead, or a draft into a publication.

Read [evidence rules](references/evidence-rules.md) whenever a claim is ambiguous or strong.

## Compose

After confirmation, write one to three concise bullets tailored to the selected target path. Each bullet should normally contain the strongest confirmed combination of context, action or responsibility, method or technique, and verifiable deliverable. Use metrics only when the user supplies them; a method, material, scope, or named deliverable is often stronger than an invented number.

Read the [resume translation method](references/resume-translation-method.md) and [role packs](references/role-packs.md) before tailoring the output. Translate the same facts by changing emphasis and ordering, not by changing what happened. Create a candidate-positioning line only when the confirmed material supports one.

If an LLM is available, read the [model writing protocol](references/model-writing-protocol.md). The model may improve wording and propose alternatives, but the fact card and validation rules remain the source of truth.

## Output format

Use this structure:

```markdown
### Confirmed fact card
- ...

### Resume bullets for <target path>
1. ...

### Rewrite comparison
- Original: ...
- Proposed: ...
- Why this is stronger: ...

### Evidence and boundaries
- Uses: ...
- Responsibility: ...
- Not claimed: ...

### Optional next questions
1. ...
```

If material facts remain unconfirmed, stop after the fact card and questions. Do not produce a ready-to-submit bullet.

## Delivery

After the user accepts the final content and explicitly asks for a file, create a local output folder containing:

```text
resume-output/
├─ resume.html
├─ resume-data.json
├─ evidence-summary.json
├─ rewrite-comparison.md
└─ export-instructions.txt
```

`resume.html` is the candidate-facing deliverable. Keep the supporting JSON and comparison files local, and do not expose their internal identifiers in the rendered resume.
