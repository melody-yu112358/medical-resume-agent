# Model writing protocol

Use this protocol only after the user has confirmed the fact card. A model can improve expression and surface missing details; it must not decide what happened.

## Inputs

Pass the model:

- one selected target path;
- the confirmed fact card, including responsibility level and evidence sources;
- the user's preferred language and length;
- an optional JD or role description;
- an optional existing bullet to improve.

Do not pass unconfirmed notes as if they were facts. If the source material is incomplete, ask questions before requesting final resume bullets.

If JD/public-evidence assistance is enabled, label role terminology separately from the confirmed fact card. It may guide emphasis and gap analysis only; it must not be used as a source for personal claims.

## Instruction contract

Use an instruction equivalent to the following:

```text
You are editing a medical resume. Use only the confirmed fact card below.
Write a fact-dependent set of non-duplicative candidate bullets for the selected target path. A well-supported flagship experience may use 5–9 and a supporting experience 3–6; use fewer when facts are sparse. Preserve responsibility
level exactly. Do not invent patient counts, study results, publications, clinical
outcomes, ownership, tools, or timelines. Treat methods, tools, techniques,
evidence resources, compliance standards, and deliverables as different kinds of
facts. If a stronger statement needs an unconfirmed detail, return a question or
[待补] rather than adding the detail.

Every bullet must identify which fact-card fields it uses. Prefer:
context or problem + personal action + method/tool/technique + confirmed deliverable.
Use an owner-level verb only when the fact card explicitly confirms that the user
made a decision, designed a bounded module, resolved a problem, or coordinated a
workstream. Otherwise use contribution-level wording such as completed, conducted,
prepared, maintained, or assisted with. Place keywords inside a grounded sentence;
never turn a tools list into a claim of expertise. Use numbers only when their
source and meaning are confirmed.
```

## Required structured response

Ask the model for JSON in this shape before rendering prose:

```json
{
  "positioning": "A conservative one-line candidate positioning, or an empty string when evidence is insufficient",
  "bullets": [
    {
      "text": "Candidate-facing resume bullet",
      "used_fact_fields": ["role", "methods", "deliverables"],
      "risk": "none | needs_confirmation",
      "question": ""
    }
  ],
  "missing_information": ["Only questions needed for a stronger, factual version"],
  "role_alignment": "Optional explanation of which supplied-JD language influenced ordering; never a personal claim"
}
```

Validate every returned bullet against the fact card before showing it. Reject or rewrite a bullet if it upgrades responsibility, invents a number or result, changes a method into a tool, or introduces a claim not grounded in a confirmed field.

Do not ask the model to manufacture a candidate positioning. It may return one only if at least two confirmed facts support the proposed domain, capability, and target direction.

## Target-specific emphasis

Change emphasis, not facts:

- **Academic progression / research application**: research question, methodological reasoning, independent learning, research potential.
- **Clinical research / hospital research**: clinical question, study execution, data quality, protocol awareness and collaboration.
- **Medical affairs / MSL**: evidence interpretation, disease-area learning, literature synthesis and accurate medical communication.
- **Health data / digital health**: data workflow, analysis logic, reproducibility, visualization and result communication.

If a target direction would require a capability that is absent from the fact card, say it is a gap; do not force a match.
