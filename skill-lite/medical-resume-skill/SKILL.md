---
name: medical-resume-skill
description: Build information-dense, evidence-bound medical resumes from confirmed experience, including conservative, professional, and high-impact versions plus printable HTML. Use for medical students or early-career researchers preparing academic applications, clinical research, medical affairs, MSL, or health-data resumes, and when polishing selected resume entries; never invent facts or inflate responsibility.
---

# Medical Resume Skill

Help the user translate real medical experience into a complete, information-dense resume for a chosen direction. Density comes from uncovering distinct factual dimensions, not repeating one fact or inventing achievements. A polished sentence is never a reason to upgrade responsibility, invent an outcome, or attach a skill the user did not use.

Choose one working mode before asking detailed questions:

- **Build from material** — turn fragments, notes, or one experience into a confirmed fact card and resume bullets.
- **Polish an existing resume** — let the user select one to three existing entries; preserve their content and improve only the selected entries.
- **Deliver a resume** — after content is accepted, assemble it into a printable HTML resume. Read [HTML delivery](references/html-delivery.md).

Then select an evidence mode:

- **Local facts only (default)** — use only material the user provides in the conversation or files they provide.
- **JD / public-evidence assistance (opt-in)** — use a user-provided JD, job URL, paper DOI, project page, or explicit permission to browse. Read [web evidence protocol](references/web-evidence-protocol.md) before browsing.

## Non-negotiable boundary

Use only confirmed personal facts. Missing information becomes a question, a `[待补]` item, or a conservative sentence; it must not become a stronger claim. Never write visible internal evidence IDs into a candidate-facing resume.

External information can improve the wording of a target role, but it cannot become evidence of the user's own experience.

## Mandatory workflow gates

Track the current stage explicitly: `intake → fact confirmation → representative sample → full composition → factual audit → delivery`. Do not skip a stage because the user asks for a file or because the source already resembles a resume.

When this Skill is hosted by the repository's web/API product, load `references/workflow-contract.json` as the machine-readable source for stage names, actions, target paths, expression tiers and privacy defaults. Do not maintain a second hard-coded workflow contract in the browser. The prose rules in this file remain authoritative for evidence and responsibility boundaries.

- During intake, read all supplied material once, preserve facts already present, list every material gap, and ask only the three highest-value unanswered questions in the current round.
- Before confirmation, split responsibility into project-level role, task-level responsibility, independently completed scope, collaborative scope, and ownership of final outputs. A general statement such as “I completed all of it” does not settle these fields.
- After confirmation, draft one representative flagship entry and ask the user to approve its density, tone and responsibility boundary before expanding the whole resume.
- Selecting professional or high-impact wording never confirms a new fact. Any new factual meaning returns to fact confirmation.
- Do not generate files until the full candidate-facing text is accepted and the factual audit is `ready`.
- After a user edits Markdown, mark it `user-edited` and rerun the factual audit before calling it ready to submit.

## Intake

Ask for the raw experience or the selected existing entry, then one target path. If the target is unclear, offer only these initial paths:

- academic progression / research application;
- clinical research / hospital research;
- medical affairs / MSL;
- health data / digital health.

For an existing resume, do not re-interview the entire person. First ask which one to three entries need work, the intended direction, and whether the user wants a light edit or a fuller fact check.

Ask whether the user wants the default local-facts mode or JD/public-evidence assistance. Do not browse without a user-provided link or explicit permission.

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

Within personal role, always record these as separate fields: project-level role, task-level responsibility, independent scope, collaborative scope, and final-output ownership.

For example, R is a programming/statistical tool, MR and Meta-analysis are analytical methods, qPCR is a wet-lab technique, GCP is a compliance framework, CRF is a clinical-research document or workflow artifact, and PubMed is an evidence-retrieval resource. Do not group them as one undifferentiated skill list. Read the [capability taxonomy](references/capability-taxonomy.md) when extracting or presenting capabilities.

## Confirmation before composition

Show the fact card and ask the user to confirm or correct it. Ask no more than three high-value follow-up questions at once. Prefer questions about responsibility, data/material source, method details, measurable results, and deliverables.

Use conservative responsibility language such as “participated”, “supported”, or “completed under supervision” when ownership is uncertain. Do not turn a collaborator into an owner, an assistant into a lead, or a draft into a publication.

Read [evidence rules](references/evidence-rules.md) whenever a claim is ambiguous or strong.

## Compose

After confirmation, read the [dense resume protocol](references/dense-resume-protocol.md). Create a content plan before writing. For every substantial experience, select distinct supported dimensions such as background, objective, responsibility, workflow, methods, tools, quality control, judgment, collaboration, deliverables, results and role relevance. Do not create separate bullets for unsupported dimensions.

When the host model is responsible for drafting, use the staged contracts in [prompt templates](references/prompt-templates.md). Do not collapse extraction, questioning, writing and audit into one unconstrained prompt. Preserve the structured output of each stage as the input to the next stage.

Generate three selectable expression tiers from the same confirmed fact set:

- **Conservative** — narrow responsibility language and the lowest inference risk.
- **Professional (default)** — confident, information-dense and suitable for normal applications.
- **High impact** — strongest defensible framing, still without changing facts or responsibility level.

A well-supported flagship experience may contain 5–9 non-duplicative bullets; a smaller experience may contain 3–6. Do not impose a fixed count when facts are sparse. Each bullet should prove a different capability or contribution and normally combine context, personal action, method/tool/technique, and a confirmed deliverable or professional purpose. Use metrics only when the user supplies them; a method, material, scope, workflow decision or named deliverable is often stronger than an invented number.

Read the [resume translation method](references/resume-translation-method.md) and [role packs](references/role-packs.md) before tailoring the output. Translate the same facts by changing emphasis and ordering, not by changing what happened. Create a candidate-positioning line only when the confirmed material supports one.

First show one representative entry. Continue to the complete content plan and three full versions only after the user accepts that sample or explicitly asks to use it as the frozen standard.


If an LLM is available, read the [model writing protocol](references/model-writing-protocol.md). Use the full [prompt templates](references/prompt-templates.md) whenever the host can preserve staged structured state. The shorter [medical resume prompts](references/medical-resume-prompts.md) are a compatibility adapter for hosts that can preserve only two stages; they must follow the same fact, density and responsibility rules. In JD/public-evidence mode, keep role language and public-source notes separate from personal facts in the final comparison.


## Output format

For a short polishing request, use this structure:

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

For a full-resume request, additionally provide:

```markdown
### Candidate positioning
...

### Content plan
- Experience: supported dimensions and omitted unknowns

### Conservative version
...

### Professional version (recommended)
...

### High-impact version
...
```

Keep all three versions on the same fact set. The user may select one complete version or accept individual bullets before delivery.

## Delivery

After the user accepts the final content and explicitly asks for a file, create a local output folder containing:

```text
resume-output/
├─ resume-editor.html
├─ resume.md
├─ resume.html
├─ resume-data.json
├─ evidence-summary.json
├─ rewrite-comparison.md
└─ export-instructions.txt
```

Read the [resume bundle contract](references/resume-data-contract.md). Store the complete conservative, professional, and high-impact resume bodies in `resume-data.json`, then run `scripts/build_resume_bundle.py`. Do not hand-code candidate text into HTML. `resume.md` is the human-editable selected version; `resume-editor.html` provides local live preview, three themes, browser-only autosave, Markdown import/download, standalone HTML export, an optional local photo, and print-to-PDF.

`resume.html` is the candidate-facing static deliverable. Keep supporting JSON and comparison files local, and do not expose their internal identifiers in the rendered resume. If the user edits Markdown, preserve that revision and audit it again rather than overwriting it with regenerated text.

For direct PDF export, run `scripts/export_resume_pdf.py`. It tries Playwright, then installed Microsoft Edge, then reports a manual browser-print fallback. Never claim that a PDF or rendered preview succeeded unless the expected file exists. When layout matters, inspect the rendered pages for overflow, clipping, broken photos, sparse trailing pages, and heading/bullet separation before delivery.

The default HTML should look complete and text-rich at first glance. Include candidate positioning, education, grouped experience sections, methods and skills, outputs/publications when confirmed, languages/certificates and research interests when supported. Do not add filler solely to occupy the page. Preserve accepted prior versions instead of overwriting them when the user requests another tier or layout.

Ask about an optional local headshot only at this delivery stage. Keep the default no-photo layout. When a user supplies an image, copy it into `resume-output/`, render the template's optional photo block using a relative local path, and record that it was user-supplied in `resume-data.json`. Do not upload the image, fetch an image from the web, or substitute a generated portrait without the user's explicit request.
