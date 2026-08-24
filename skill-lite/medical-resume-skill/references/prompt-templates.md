# Prompt contracts for dense medical resumes

Use these contracts when the host agent or model performs the writing. Replace bracketed inputs with conversation data. Run stages in order; do not ask one prompt to infer facts and produce a final resume simultaneously.

## Stage 1: fact extraction and questions

```text
You are the fact-extraction stage of a medical resume workflow.

Input:
- Raw user material: [RAW_MATERIAL]
- Target direction, if supplied: [TARGET]
- Previously confirmed facts: [CONFIRMED_FACTS]
- Questions already asked: [PREVIOUS_QUESTIONS]

Separate personal facts into: context/topic, objective, responsibility,
actions, methods/study designs, tools/databases, experimental techniques,
clinical/compliance work, workflow, quality control, decisions, collaboration,
deliverables/results, dates/scope, and evidence source.

Do not infer a missing action, method, number, publication, outcome, ownership,
skill level or disease area. Mark ambiguity explicitly. Select no more than three
new questions with the greatest expected improvement to resume quality. Prefer
responsibility, concrete workflow, deliverable/result and method/tool boundaries.

Read all supplied material before asking. Do not ask for a fact already present.
List every material gap internally, but return only the three highest-value new
questions in this round. Split responsibility into project-level role, task-level
responsibility, independent scope, collaborative scope, and final-output ownership.
Do not treat a general statement such as "I completed all of it" as confirmation
of every responsibility field.

Return JSON only:
{
  "fact_card": {},
  "confirmed": [],
  "uncertain": [],
  "questions": [],
  "ready_for_confirmation": false
}
```

Stop after this stage until the user confirms or edits the fact card.

## Stage 2: representative sample

```text
Use only the confirmed fact card to draft one flagship experience as a small
representative sample. Show its planned dimensions and professional-tier bullets.
Ask the user to approve density, tone, responsibility language, and layout order.
Do not draft the complete resume until this sample is accepted or the user
explicitly freezes it as the standard.
```

## Stage 3: positioning and content plan

```text
You are the planning stage of an evidence-bound medical resume workflow.
Use only the confirmed fact card below.

Confirmed fact card: [CONFIRMED_FACT_CARD]
Target direction: [TARGET]

Create a conservative one-line candidate positioning only if at least two
confirmed facts support the domain, capability and target. For each experience,
select supported dimensions from: background, objective, responsibility,
workflow, method, tool/technique, quality/compliance, judgment, collaboration,
deliverable/result, and role relevance.

Allocate 5-9 dimensions to a well-supported flagship experience, 3-6 to a
supporting experience, and fewer to sparse material. Never manufacture a
dimension to reach a count. Each planned item must cite source fact fields.

Return JSON only:
{
  "positioning": "",
  "profile_summary_plan": [],
  "experiences": [
    {
      "experience_id": "",
      "selected_dimensions": [
        {"dimension_id": "", "source_fact_fields": [], "purpose": ""}
      ],
      "omitted_unknowns": []
    }
  ]
}
```

## Stage 4: three expression tiers

```text
You are the writing stage of an evidence-bound medical resume workflow.

Confirmed fact card: [CONFIRMED_FACT_CARD]
Approved content plan: [CONTENT_PLAN]
Target direction: [TARGET]
Language: [LANGUAGE]

Generate conservative, professional and high-impact versions from exactly the
same fact set. Preserve every number, method, tool, outcome and responsibility
boundary. Professional is the default. High impact may strengthen framing,
ordering and professional relevance, but may not convert participation into
ownership or professional interpretation into a factual result.

Tier selection is an expression choice, not fact confirmation. If any tier needs
a new factual meaning, return that item to the confirmation stage.

Write one non-duplicative bullet for each planned dimension. Put technical
keywords inside evidence-bearing sentences. Do not output internal enum values.

Return JSON only:
{
  "conservative": {"positioning": "", "experiences": []},
  "professional": {"positioning": "", "experiences": []},
  "high_impact": {"positioning": "", "experiences": []}
}

Each bullet object must contain:
{"dimension_id": "", "text": "", "source_fact_fields": [], "risk": "none"}
```

## Stage 5: independent factual audit

```text
Audit the proposed resume against the confirmed fact card. Do not improve its
style during this pass.

Confirmed fact card: [CONFIRMED_FACT_CARD]
Proposed resume JSON: [RESUME_JSON]

Reject a bullet if it introduces or upgrades any number, action, method, tool,
technique, result, publication status, responsibility, timeline or clinical
impact. Flag duplicates that prove the same capability from the same evidence.
Flag internal enum leakage, awkward Chinese-English joins and unsupported
self-praise. Return corrected text only when the factual meaning remains equal.

Return JSON only:
{
  "status": "ready|revision_required",
  "checks": [],
  "rejected_items": [],
  "safe_corrections": []
}
```

## Stage 6: data-driven delivery

```text
Store all three complete candidate-facing resume bodies in resume-data.json.
Set selected_tier to the user-accepted version, then run the bundled deterministic
builder to produce resume.md, resume.html and resume-editor.html. Use resume data
as the only candidate-information source. Never hand-code candidate text into
HTML. Remove unsupported sections instead of leaving placeholders. Do not expose
evidence IDs, audit notes, risk labels or [待补]. If the user edits Markdown, mark
the result user-edited and audit it again before final delivery.
```

These prompts are contracts, not hidden evidence. If the host cannot preserve structured state between stages, keep the fact card and content plan visibly in the conversation and ask the user to confirm again before final delivery.
