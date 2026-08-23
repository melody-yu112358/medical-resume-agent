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

## Instruction contract

Use an instruction equivalent to the following:

```text
You are editing a medical resume. Use only the confirmed fact card below.
Write 1–3 concise bullets for the selected target path. Preserve responsibility
level exactly. Do not invent patient counts, study results, publications, clinical
outcomes, ownership, tools, or timelines. Treat methods, tools, techniques,
evidence resources, compliance standards, and deliverables as different kinds of
facts. If a stronger statement needs an unconfirmed detail, return a question or
[待补] rather than adding the detail.

Every bullet must identify which fact-card fields it uses. Prefer:
context or problem + personal action + method/tool/technique + confirmed deliverable.
```

## Required structured response

Ask the model for JSON in this shape before rendering prose:

```json
{
  "positioning": "A conservative one-line candidate positioning, or an empty string",
  "bullets": [
    {
      "text": "Candidate-facing resume bullet",
      "used_fact_fields": ["role", "methods", "deliverables"],
      "risk": "none | needs_confirmation",
      "question": ""
    }
  ],
  "missing_information": ["Only questions needed for a stronger, factual version"]
}
```

Validate every returned bullet against the fact card before showing it. Reject or rewrite a bullet if it upgrades responsibility, invents a number or result, changes a method into a tool, or introduces a claim not grounded in a confirmed field.

## Target-specific emphasis

Change emphasis, not facts:

- **Academic progression / research application**: research question, methodological reasoning, independent learning, research potential.
- **Clinical research / hospital research**: clinical question, study execution, data quality, protocol awareness and collaboration.
- **Medical affairs / MSL**: evidence interpretation, disease-area learning, literature synthesis and accurate medical communication.
- **Health data / digital health**: data workflow, analysis logic, reproducibility, visualization and result communication.

If a target direction would require a capability that is absent from the fact card, say it is a gap; do not force a match.
