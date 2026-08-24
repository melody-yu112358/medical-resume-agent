# HTML delivery

Generate a file only after the user has accepted the content and explicitly asks for a local deliverable. The default deliverable is one printable, single-column A4 HTML resume. It is designed for formal academic and medical applications, not for reproducing a screenshot or a Canva-style layout.

## Required files

Create a local `resume-output/` directory with:

- `resume-editor.html` — a local Markdown editor with live A4 preview;
- `resume.md` — the selected, human-editable resume body;
- `resume.html` — the final candidate-facing resume;
- `resume-data.json` — the structured data used to render it;
- `evidence-summary.json` — confirmed facts and evidence notes;
- `rewrite-comparison.md` — original text, accepted rewrite, and rationale;
- `export-instructions.txt` — concise browser print-to-PDF steps.

Use the included [ATS medical resume template](../assets/ats-medical-resume.html) for compatibility or the bundled editor for editable delivery. Follow the [resume bundle contract](resume-data-contract.md) and use `scripts/build_resume_bundle.py`; do not duplicate candidate text by hand across Markdown, JSON and HTML.

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

The user may edit `resume.md` or use `resume-editor.html`. The editor is self-contained, loads no third-party scripts, stores drafts only in the current browser, supports three themes, and can export Markdown or standalone HTML. Treat a changed resume as `user-edited`; run the factual audit before calling it final, then store the accepted text back in the corresponding tier of `resume-data.json` and rebuild.

For PDF, first try `scripts/export_resume_pdf.py resume-output/resume.html`. The script uses Playwright when available, then installed Microsoft Edge, and otherwise exits with a manual-print instruction. A failed browser or missing output file is a failed export, not a delivered PDF. Inspect rendered pages before delivery; check clipping, overflow, broken photos, awkward page breaks and a sparse final page.
