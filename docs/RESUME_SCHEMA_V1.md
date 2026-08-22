# Resume document schema v1

`schemas/resume_document.schema.json` is the shared contract between the file
importer, evidence review, JD tailoring, and resume renderer. It deliberately
does not prescribe an HTML, DOCX, or PDF template.

## Contract rules

1. A parser may create `extracted` evidence but must retain its source document
   and a page, paragraph, or character-range locator.
2. A model may create `model_draft` text but cannot promote evidence to
   `user_confirmed`.
3. A renderer may use only `user_confirmed` evidence by default. It must not
   turn missing fields into claims.
4. A rewritten bullet and its parent experience both cite `evidence_ids`.
   This keeps a future accept/reject audit attributable after editing.
5. Source documents identify where a fact came from; they do not require
   retaining the uploaded file after extraction.

## Medical sections

The top-level sections distinguish education, clinical rotations or clinical
work, professional experience, research, projects, publications, awards,
skills, and languages. This prevents research and clinical materials from
being collapsed into a generic date-led experience list.

`target.purpose` supports 保研/夏令营、考研复试、考博、医院/规培校招、医药健康行业校招、社招和通用简历. The purpose selects a section-order policy; it does not change the
underlying evidence.

## Integration sequence

1. File upload returns raw text plus source locators.
2. The deterministic `/api/resume-structures` parser groups explicit Chinese
   headings and emits candidates with `extracted` evidence. It does not infer
   organizations, roles, authorship, dates, or achievements that are absent.
3. The user confirms, edits, or rejects candidates.
4. JD matching and constrained rewriting consume confirmed evidence.
5. Each visual template renders the same structured document with its own
   section order and layout.

The synthetic sample at `tests/fixtures/resume_document.sample.json` is a
safe contract fixture. Do not place real resumes or API credentials in the
repository.
