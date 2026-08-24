# Resume bundle contract

Use this contract for full-resume delivery. Candidate information must flow from the accepted tier in `resume-data.json`; never type candidate facts directly into generated HTML.

## Required data

```json
{
  "schema_version": "medical-resume-data-v1",
  "candidate": {
    "name": "",
    "target_direction": "",
    "contact": "",
    "photo": null
  },
  "fact_card": {},
  "tiers": {
    "conservative": {"markdown": ""},
    "professional": {"markdown": ""},
    "high_impact": {"markdown": ""}
  },
  "selected_tier": "professional",
  "theme": "clinical-blue",
  "edit_status": "generated",
  "audit": {"status": "ready"}
}
```

All three `markdown` values must contain the complete candidate-facing resume for that tier, not labels, status messages, or references to another file. `selected_tier` controls the initial `resume.md`, `resume.html`, and editor preview. Supported themes are `clinical-blue`, `academic-green`, and `ats-mono`.

`fact_card` and the evidence files remain local audit material. Do not display them in the resume. Tier selection changes expression only; it never confirms a new fact. If the user edits `resume.md` or the browser editor, set `edit_status` to `user-edited` and run the factual audit again before calling the result ready to submit.

## Deterministic delivery

Run:

```text
python scripts/build_resume_bundle.py resume-data.json --output resume-output
```

The tool creates `resume.md`, `resume.html`, and `resume-editor.html` from the selected tier. It does not invent, rewrite, or complete content. Copy the remaining evidence and comparison files into the same directory.
