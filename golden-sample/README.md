# V3.2 medical resume golden sample

This directory contains the frozen quality reference used to evaluate dense medical-resume generation.

## Human-authored reference

- `v3.2-professional.md` and `v3.2-professional.html`: default professional tier.
- `v3.2-professional-no-avatar.html`: professional tier without a photo.
- `v3.2-high-impact.md`: strongest defensible expression tier.
- `v3.2-fact-mapping.md`: mapping from visible content to confirmed facts.
- `v3.2-review-conclusion.md`: HR and academic-review conclusions.

## Generated regression artifacts

- `generated/v3.2-professional-generated.html`
- `generated/v3.2-resume-document.json`

The generated files must be produced through the structured pipeline. They must not be copied from the human-authored HTML. Run `python scripts/verify_v32_generated_quality.py` to check bullet counts, dimension uniqueness, factual boundaries, data-driven rendering, avatar paths and visible information density.

The golden sample is a quality standard, not a source of facts for other users. Ordinary input must never inherit its disease area, tools, numbers, outputs or responsibility level.
