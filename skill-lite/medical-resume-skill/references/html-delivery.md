# HTML delivery

Generate a file only after the user has accepted the content and explicitly asks for a local deliverable. The default deliverable is one printable, single-column A4 HTML resume. It is designed for formal academic and medical applications, not for reproducing a screenshot or a Canva-style layout.

## Required files

Create a local `resume-output/` directory with:

- `resume.html` — the final candidate-facing resume;
- `resume-data.json` — the structured data used to render it;
- `evidence-summary.json` — confirmed facts and evidence notes;
- `rewrite-comparison.md` — original text, accepted rewrite, and rationale;
- `export-instructions.txt` — concise browser print-to-PDF steps.

Use the included [ATS medical resume template](../assets/ats-medical-resume.html) as the starting layout. Replace all `{{placeholders}}`; do not leave example text or internal IDs in the final file.

When the user opts in to a photo, also place a copy of the supplied local image in this directory, for example `profile-photo.jpg`. Use a relative path in `resume.html`; the image must not be uploaded or embedded from a third-party URL.

## Layout rules

- Use one column, A4 page size, white background and high-contrast text.
- For students and early-career researchers, place education before experience unless the user asks otherwise.
- Use a compact header with name, target direction and contact details. Do not use a photo by default.
- Ask about an optional photo only after the user has accepted the resume content and requested a file. If they provide a local image, render it with the `{{optional_photo_html}}` placeholder, for example `<figure class="profile-photo"><img src="profile-photo.jpg" alt="证件照"></figure>`. Otherwise replace that placeholder with an empty string; do not leave an empty frame.
- A formal headshot is appropriate for some Chinese applications. A clearly de-identified illustration may be used in a product demo, but must never be silently substituted for a user's photo.
- For every experience, display organisation or project on the left and dates on the right; put role and research topic on a muted second line.
- Render separate research, project and clinical sections when the confirmed material supports them. Remove an unsupported section rather than leaving a placeholder.
- Use the accepted professional tier by default; keep conservative and high-impact source versions in `resume-data.json` so another version can be rendered without rewriting facts.
- Keep bullets below their corresponding experience. Do not repeat the same bullet in skills and experience.
- Present methods, tools, experimental techniques and certificates as concise grouped text or one item per line, not as decorative chips.
- Do not show `ev_001`, risk levels, source quotes, audit records, `[待补]`, or any other internal review text in the visible resume.
- Use browser print settings: A4, default margins or narrower, background graphics enabled only if the theme needs them, and scale 100%.

## Editing after delivery

If the user asks for an edit, update `resume-data.json` first, then regenerate `resume.html`. This keeps the rendered file and the factual source aligned.
