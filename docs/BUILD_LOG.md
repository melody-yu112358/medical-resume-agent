# Project build log

## 2026-08-22 — Medical Experience Compiler v1

### Added

- Implemented Experience Draft Service with deterministic extraction of medical research facts from raw experience text.
- Added support for four role packs: `doctoral_v1`, `clinical_research_v1`, `medical_affairs_v1`, and `health_ai_data_v1`.
- Created bullet composer that generates 1-3 candidate bullet points per role pack from canonical experience.
- Implemented claim ledger with audit trail for tracking bullet claims and user dispositions.
- Added claim gate with twelve deterministic validation checks to ensure factual accuracy and prevent fabrication.
- Built browser-based experience compiler demo at `/demo/experience-compiler/index.html` with complete workflow.
- Added the meta-analysis example and six additional end-to-end fixtures: clinical research, data analysis, wet lab, information insufficient, medical writing, responsibility ambiguous, and user exaggeration.

### Verification

- All 205 Python tests pass, including comprehensive coverage for experience drafting, confirmation, bullet composition, claim validation, claim ledger, schema contracts, API endpoints, and the end-to-end example fixtures.
- The four role packs and every fixture produce distinct but fact-equivalent expressions, keep conservative responsibility levels, omit unknown items, and avoid all forbidden outputs.
- Browser-tested the synthetic Meta analysis example through the complete workflow: fact extraction, clarification questions, confirmation, bullet generation, and export.
- Verified the three compiler API endpoints (`/api/experience-drafts`, `/api/experience-confirmations`, `/api/bullet-composer`) serve the demo end to end.
- Verified deterministic behavior without LLM dependency while maintaining optional LLM integration for natural language expression.

## 2026-08-21 — user-saved browser resume versions

### Added

- Added explicit local version saving for the final resume. A version records
  its user-provided name, purpose, visual template, target role, timestamp,
  and final text only after the user presses the save button.
- Added a small local version list plus latest-version loading with an
  overwrite confirmation when the editor already contains text.
- Versions are stored only in the current browser; no version is uploaded or
  retained by the server in this beta.

### Follow-up

- Per-suggestion accept/reject audit records for AI rewrites remain the next
  implementation step. They are intentionally not claimed as complete here.

## 2026-08-21 — local rewrite disposition audit

### Added

- Replaced automatic rewrite insertion with an explicit user choice:
  **accept and insert** or **do not use**.
- Each decision writes a browser-local audit event with suggestion ID,
  disposition, timestamp, matched requirement, source-evidence presence, and
  output length. The audit deliberately avoids retaining the full source or
  rewritten personal text a second time.
- The corresponding suggestion card now visibly records its accepted or
  rejected state in the active session. A failed browser save does not block
  the user's chosen action, but it is disclosed in the interface.

### Verification

- JavaScript syntax and whitespace validation passed.
- The browser correctly handled an unavailable model service without exposing
  any accept/reject controls. End-to-end interaction verification remains
  pending until the configured model endpoint is reachable again.

## 2026-08-21 — distinct resume preview layouts

### Added

- Replaced the former colour-only template treatment with three distinct
  preview structures: clinical blue uses a chronological, optional-photo
  layout; academic green uses a research/evidence main column with a compact
  competency sidebar; ATS minimal is a single-column black-and-white layout
  without a photo.
- Kept purpose selection independent from visual choice. Switching a template
  changes presentation and section placement only; it does not create or
  suppress resume facts.
- Updated the template picker labels to communicate the intended use of each
  layout rather than only its colour.

### Verification

- JavaScript syntax and whitespace validation passed.
- Browser-tested a synthetic MSL example: clinical preview included the photo
  placeholder, academic preview rendered the research layout and sidebar, and
  ATS preview rendered the photo-free minimal header.

## 2026-08-21 — local structured resume editor v1

### Added

- Added a medical-field editor after structure confirmation. Confirmed content
  can now be organized as education, clinical experience, work experience,
  research, projects, publications, awards, skills, or languages.
- The editor deliberately leaves key fields blank until the user fills them;
  recognised source lines remain visible as evidence and are not used to
  silently guess an institution, role, department, author position, or date.
- Saving creates a browser-local `resume-document-editor-v1` draft containing
  the selected evidence IDs, user-entered fields, purpose, and basic details.
  It is not represented as a valid `resume-document-v1` until formal schema
  conversion and field validation are added.
- Tailored-document generation now prefers the saved, user-confirmed fields;
  raw source lines remain available as detail bullets only when they do not
  duplicate a typed structured heading. Skills and language entries support
  one item per line.

### Verification

- Full Python test suite passed (47 tests).
- JavaScript syntax check and whitespace validation passed.
- Browser-tested the synthetic example through structure selection, field
  entry, browser-local draft save, diagnosis, and tailored-document generation.
  The generated education, research, and skills sections reflected saved
  fields and preserved confirmed research-detail bullets.

## 2026-08-21 — resume structure confirmation UI

### Added

- Added a mandatory structure-confirmation step between raw resume input and
  tailored-document generation in `demo/resume-beta`.
- The page now calls `POST /api/resume-structures`, displays recognised medical
  sections, and lets the user select exactly which extracted lines may enter a
  generated document. Unclassified lines are displayed but never included
  automatically.
- A new upload or an edit to the pasted resume clears previous selections.
- Tailored documents now use selected source lines by section rather than
  repeating the entire original resume under each heading. JD keywords are no
  longer used as fallback skills in the tailored document or preview.
- Added compatibility for the existing `科研 / 实践经历` heading.

### Verification

- Full Python test suite passed (47 tests).
- JavaScript syntax check passed.
- Browser-tested the synthetic example: education, research, and skills were
  separated; seven selected source lines produced a tailored draft without
  injecting JD-only statements.

## 2026-08-21 — traceable medical resume schema v1

### Added

- Added `schemas/resume_document.schema.json`, the shared data contract for
  imported resumes, evidence confirmation, JD tailoring, and visual rendering.
- Distinguished education, clinical experience, professional experience,
  research, projects, publications, awards, skills, and languages instead of
  treating every item as a date-led generic experience.
- Required every displayable experience, bullet, skill, language, and
  publication to reference one or more evidence IDs. Evidence preserves an
  optional source document and page, paragraph, or character-range locator.
- Added review-event fields for future per-suggestion accept/reject/edited
  audit records. A model draft cannot become confirmed evidence by itself.
- Added a synthetic medical-resume fixture and contract tests; no real resume
  data was added to the repository.

### Verification

- JSON contract files parse successfully.
- Full Python test suite passed (38 tests, including 2 resume-schema contract
  tests and 3 existing resume-intake tests).

### Follow-up implementation

- Added the deterministic `POST /api/resume-structures` endpoint. It groups
  explicit Chinese headings into medical sections and returns imported lines as
  `extracted` evidence with line locators.
- The endpoint deliberately leaves unknown lines unclassified and returns
  confirmation questions. It does not infer organizations, roles, dates,
  author positions, or achievements from ambiguous text.

## 2026-08-20 — resume agent product slice

### Completed and merged

- Added the medical resume page with deterministic JD evidence matching,
  optional grounded model rewriting, final-text risk review, editable output,
  and A4 browser print preview.
- Added purpose selection for 保研/夏令营、考研复试、考博、校招、社招和通用简历, plus three visual styles.
- The purpose selector currently changes the composition structure and prompt
  focus while preserving the career-exploration handoff into the resume page.

### Deliberately not yet synchronised from the standalone resume repository

- Dynamic purpose-specific preview rendering (different section order).
- Medical split of 校招 into 医院/规培校招 and 医药健康行业校招, with specialised material checklists.
- Browser-local master evidence bank and named resume-version storage.
- Per-suggestion accept/reject audit history for AI rewrites.

### Verification

- The merged resume slice passed 36 Python tests and a JavaScript syntax check.

## Purpose

This is the source document for a future product and technical handbook. It
records what changed, why the team chose it, what failed, and how the result was
checked. Add an entry for each meaningful pull request; do not rewrite earlier
decisions without leaving a new dated note.

## Technical baseline

The repository currently has three distinct layers of work:

1. static browser demos in `demo/` for product exploration;
2. a deterministic Flask architecture slice for
   `resume + job_id -> evidence match report`;
3. product, privacy, data-contract, and acceptance documents in `docs/` and
   `schemas/`.

The project follows a "deterministic skeleton plus optional LLM generation"
boundary. Code applies constraints, calculates scores, checks references, and
preserves traceability. A future model may extract structured evidence, ask
questions, and explain results, but it must not invent user or market facts.

## 2026-08-16 — product vision and MVP scope

### Change

- Created branch `melody/product-vision` from `main`.
- Expanded `PRODUCT.md`, `WORKFLOW.md`, and `ACCEPTANCE.md`.
- Defined the first loop as profile evidence -> career hypotheses -> seven-day
  experiment -> outcome review -> updated profile and hypothesis.
- Added early exit, counter-evidence, checkpoints, and evidence provenance.
- Committed as `98d0e7d Clarify product vision and MVP scope`.
- Pull request #4 was merged to `main` as `6f696b9`.

### Problem: Windows line-ending warnings

Git warned that LF would be replaced by CRLF. This was a line-ending notice,
not lost content. `git diff --check` passed, so the documentation change was
kept without a repository-wide line-ending refactor.

### Problem: GitHub HTTPS connection

Normal `push` and `pull` failed with either an offline Windows certificate
revocation check or a timeout to `github.com:443`. The successful operation used
one-off Git configuration for the command only:

```powershell
git -c http.sslBackend=schannel `
    -c http.schannelCheckRevoke=false `
    -c http.curloptResolve=github.com:443:<verified-GitHub-IP> `
    push -u origin <branch>
```

The same pattern was later used for `pull --ff-only origin main`. The resolved
IP is deliberately not stored because GitHub nodes can change. No permanent
proxy setting was added, and `http.sslVerify=false` was not used. Certificate
revocation checking was disabled only for the affected command.

## 2026-08-17 — career-card scope and pilot

### Starting state

- `main` was synchronised to merge commit `6f696b9`.
- The static demo contained five hard-coded illustrative careers.
- The backend contained one synthetic medical-affairs job and deterministic
  matching tests.
- No reviewed career record existed.

### Product problems found

1. The product document listed both MSL and medical affairs, while the demo
   used medical affairs and healthcare product. The levels were inconsistent.
2. "Healthcare AI" was meaningful to the product story but too broad to be one
   career card.
3. Job postings were easy to find but often employer-specific, temporary,
   duplicated, blocked, or missing a publication date.

### Decisions

- Created branch `melody/career-cards-v0-1`.
- Standardised the first scope to MSL, CRA, pharmacovigilance specialist,
  medical writer, and healthcare AI product manager.
- Kept medical affairs, clinical research, drug safety, and healthcare AI as
  career families rather than duplicate cards.
- Used healthcare AI product manager as the first AI role because it has a
  searchable title and a coherent task boundary. Algorithm, data, evaluation,
  and other AI roles remain future cards.
- Created `docs/CAREER_CARDS.md` and the first draft card,
  `healthcare-ai-product-manager.cn.json`.
- Committed the scope, guide, and pilot as
  `8578231 Define career card scope and add AI pilot`.

### Data construction

Each career card conforms to `schemas/career.schema.json`:

```text
career identity and market
  -> sourced tasks and requirements
  -> transferable-skill inferences
  -> work environment and entry barriers
  -> validation actions
  -> source metadata and review status
```

Claims store `source_ids`, a claim type, and confidence. Sources store the
publisher, URL, publication date when known, access date, and jurisdiction.
Cards stay `draft` until another team member checks them.

### Research problems and responses

- **Broad search results:** narrowed searches with exact role names, employer
  domains, `gov.cn`, and `edu.cn`.
- **Blocked first-party pages:** did not bypass access controls; used an
  employer's public alternative, university-hosted employer post, or another
  source.
- **Conflicting qualifications:** recorded ranges and employer variation rather
  than promoting the strictest sample to a universal rule.
- **Old or missing dates:** stored `null` when the date was unknown and avoided
  using stale numbers as current market facts.
- **Platform copyright:** stored paraphrased atomic claims and metadata rather
  than copies of complete job descriptions.

### Verification

The pilot was checked with:

```powershell
python -m unittest discover -s tests
```

Additional checks validated the JSON against `career.schema.json` and confirmed
that every claim's `source_ids` existed in the same card. Four repository tests
passed.

## 2026-08-17 — synthetic profiles and evaluation boundaries

### Starting state

- Pull request #5 was merged to `main` as `f41bad1`.
- Five source-backed career cards existed, but there were no structured user
  profiles against which to test them.
- The implemented backend could compare a resume with one synthetic job, but
  it could not yet produce career hypotheses from the new career cards.

### Decisions

- Created branch `melody/synthetic-profiles-v0-1` from the merged `main`.
- Added three fully fictional profiles covering clinical communication,
  research/product exploration, and safety/research coordination.
- Added stable `evidence_id` values and optional context, task, action, result,
  artifact, and capability fields to the medical-profile contract so future
  hypotheses can point back to exact personal evidence.
- Marked every committed profile explicitly as `synthetic`; none represents a
  real person or a typical member of a student group.
- Added expected hypotheses as evaluation boundaries rather than fixed labels
  or rankings. Each hypothesis includes supporting evidence IDs,
  counter-evidence, unknowns, and a validation action.
- Added forbidden conclusions and constraint checks to detect invented support,
  hidden conflicts, and verdict language.
- Kept this change at the data-contract and evaluation-fixture layer. It does
  not yet implement career comparison, ranking, API endpoints, or LLM calls.

### Verification

- All three profiles passed `medical_profile.schema.json` validation.
- Evaluation cases reference existing profile evidence and career-card IDs.
- The new tests and the existing backend tests passed: six tests total.
- `git diff --check` passed; the Windows LF-to-CRLF notice remains informational.

## 2026-08-17 — deterministic career comparison v0.1

### Starting state

- Pull request #6 was open for review and had not yet been merged.
- Work continued on stacked branch `melody/career-comparison-v0-1` from commit
  `329bd27`; the branch therefore temporarily depends on PR #6.
- The backend supported `resume + one synthetic job -> match report`, but not
  `structured profile + career library -> career hypotheses`.

### Decisions

- Preserved the existing resume-to-job flow and added a separate career
  exploration application service.
- Added JSON repositories for structured medical profiles and sourced career
  cards behind repository protocols.
- Added explicit capability groups and transparent integer weights. Only
  evidence capabilities participate; interests and degrees do not receive
  points by themselves.
- Named the result `evidence_coverage_percent`, not fit or suitability. Each
  component exposes its weight, matched profile evidence IDs and career source
  IDs.
- Limited output to three revisable hypotheses containing support,
  source-backed counter-evidence, gaps, unknowns, constraint findings and one
  career-card validation action.
- Added cautious travel handling. A non-negotiable against frequent travel
  deprioritizes CRA or MSL when the career card supports a potential conflict,
  but does not claim a universal travel frequency.
- Kept preferred-city availability unknown because a career card is not a live
  job listing.
- Did not add an API endpoint, frontend change, LLM call, salary conclusion or
  personality inference in this slice.

### Verification

- The clinical communication profile ranked MSL first.
- The research/product profile ranked healthcare AI product manager first.
- The safety/coordination profile ranked pharmacovigilance specialist first.
- Expected hypotheses remained within the three-result limit.
- Profile evidence and career source references were checked for integrity.
- Travel non-negotiables reduced affected evidence coverage before ranking.
- The new and existing tests passed: ten tests total.

## 2026-08-17 — comparison API, integration page and bounded LLM

### API and frontend connection

- Added `GET /api/profiles` for source-controlled synthetic profile summaries.
- Added deterministic `POST /api/career-comparisons`.
- Added an independent integration page under `/demo/` instead of modifying the
  collaborator's existing static workbench.
- The page displays support, gaps, unknowns, constraints and a validation action
  for each hypothesis. It labels the percentage as evidence coverage rather
  than fit.

### Model boundary

- Added an OpenAI-compatible Chat Completions adapter using the Python standard
  library, with base URL, API key and model supplied only through local
  environment configuration.
- Added `POST /api/career-explanations`. The endpoint always runs deterministic
  comparison first and returns model wording separately from the comparison.
- Restricted the model to language explanation. It cannot alter ranking,
  coverage, constraints, profile evidence or career records.
- Added an output gate that requires career names and profile evidence IDs and
  rejects verdict language, unapproved percentages and added URLs.
- Kept deterministic comparison available when no model is configured. Model
  network failures and rejected output return errors rather than fallback
  invention.
- No real personal data was used or sent to a model.

### Verification

- API tests cover profile listing, comparison, demo delivery and invalid input.
- A fake compliant model passes the explanation boundary.
- A fake model using fixed-fit language is rejected.
- All existing and new tests passed: fifteen tests total before final file and
  formatting checks.

### First live-model compatibility finding

- The first authenticated DeepSeek V4 Flash request reached the API but returned
  empty final `content`; the gateway correctly rejected it instead of showing a
  fallback answer.
- Official documentation showed that DeepSeek V4 defaults to thinking mode.
  The explanation adapter now sends `thinking: disabled` only for the official
  `api.deepseek.com` host, leaving generic compatible providers unchanged.
- A second authenticated request then returned HTTP 200. Its explanation passed
  the quality gate and cited all four evidence IDs from the selected synthetic
  profile.
- The live check used synthetic data only. The API key was neither printed nor
  written to the log. Mojibake in the PowerShell preview was limited to terminal
  rendering; the integration page serves and displays UTF-8.

## Next planned entries

- Complete and review all five draft career cards.
- Test with consenting users while keeping real personal data outside Git.

## 2026-08-17 — transient profile intake and confirmation checkpoint

### Starting state

- The synthetic comparison and bounded explanation path worked end to end.
- Users could select only three source-controlled fictional profiles, so the
  result demonstrated architecture but did not yet respond to a user's own
  experience.

### Decisions

- Added a separate local intake page instead of replacing the synthetic test
  page.
- Required explicit acknowledgement before sending experience text to the
  configured model and warned against entering patient or third-party
  identifiers.
- Restricted the model to JSON evidence extraction using a fixed capability
  vocabulary. Every proposed evidence item must quote a continuous substring
  of the user's text; ungrounded quotes reject the whole draft.
- Marked all extracted evidence `unverified`. Users must confirm each item and
  may remove or add capability labels before comparison.
- Kept confirmed profiles transient by carrying them in the comparison request.
  No participant input is written to `data/`, Git or a database.
- Reused the existing deterministic comparator and bounded explanation layer;
  the model still cannot change career order or evidence coverage.

### Verification

- Added tests for grounded quotes, rejection of invented quotes, explicit
  confirmation and comparison of a transient profile.
- JavaScript syntax validation passed.
- All 22 repository tests passed.
- One live DeepSeek check used a completely fictional experience. It returned
  three evidence items, every quote was present in the supplied text, and the
  resulting draft reported `persisted: false`.

## 2026-08-17 — progressive three-level journey shell

### Product decisions

- Defined the possibility glimpse, fifteen-minute career exploration and
  seven-day experiment as checkpoints in one evidence journey rather than
  three independent products.
- Limited the glimpse to three light questions. It returns unverified
  capability clues, career worlds and one unknown question without scores,
  rankings or a best-fit role.
- Reused the grounded profile-intake and deterministic comparison flow as the
  fifteen-minute experience instead of creating a second implementation.
- Made explicit hypothesis selection a prerequisite for the seven-day level.
  The deep experience is an action and review workspace, not a longer
  questionnaire.
- Recorded the shared state, transitions, stopping rules and acceptance
  criteria in `docs/JOURNEY_LEVELS.md`.

### Interface and routing

- Replaced the engineering comparison page at `/demo/` with a user-facing
  journey entry page offering all three depths.
- Added a deterministic, browser-only possibility glimpse and a preview of the
  seven-day experiment workspace under `demo/journey/`.
- Added shared journey navigation to the existing profile-intake page.
- Preserved the original synthetic engineering validation page at
  `/demo/integration.html`.
- Used a warm editorial visual system to communicate reflection and
  reliability rather than a generic technology dashboard.

### Visual issue found during review

- The first navigation treatment used a translucent background on a centered
  container. The page gradient showed through unevenly and the color did not
  cover the full viewport width.
- Changed the navigation to a full-width solid warm background while retaining
  alignment with the main content. Applied the same treatment to the journey
  and profile-intake pages.

### Verification

- Confirmed all journey HTML, CSS and JavaScript assets return HTTP 200 through
  the Flask demo routes.
- JavaScript syntax validation passed.
- Browser review confirmed the corrected full-width navigation treatment.
- All 29 repository tests passed.

## 2026-08-17 — pivot from seven-day validation to application preparation

### Product decision

- After team discussion, replaced the planned seven-day experiment in the
  first milestone with a concrete application-preparation path.
- The updated path is confirmed profile evidence -> career hypotheses ->
  sourced real-job shortlist -> selected JD -> grounded resume revision -> HR
  screening practice and feedback.
- Kept the possibility glimpse and career-exploration checkpoints. Users may
  still pause, reject every direction, or stay in medicine without being
  treated as failed users.
- Career cards remain direction-level knowledge and may not masquerade as
  specific job postings.
- Resume wording and interview feedback must remain traceable to the stored JD
  and confirmed user evidence. The product does not estimate hiring probability.

This entry records a forward-looking scope change and does not rewrite the
earlier seven-day experiment decisions. The existing experiment preview remains
temporary until the user-facing pages are updated in a later change.

## 2026-08-21 — formal resume document rendering and English headings

### Product decisions

- Replaced the browser-only `resume-document-editor-v1` draft shape with the
  repository's formal `resume-document-v1` shape when the user saves confirmed
  fields.
- Made the print preview preferentially render that saved structured document,
  rather than parsing the generated long-form text back into sections.
- Added common English headings for education, clinical rotations, work,
  research, projects, publications, awards, skills and languages. Imported
  English statements remain unchanged; this is recognition support, not
  automatic translation.

### Verification

- Added a deterministic English-heading structurer test.
- All 48 Python tests passed.
- JavaScript syntax and whitespace checks passed.
- Browser-tested a synthetic English resume through structure confirmation,
  structured save and the clinical preview. The preview reported that it read
  confirmed structured data directly; no browser console errors were present.

## 2026-08-21 — evidence-backed medical capability profile

### Product decisions

- Added a deterministic capability candidate layer for medical research and
  clinical-research resumes. It recognizes only methods and techniques named
  in user-confirmed evidence; it does not infer proficiency from a keyword.
- Candidates include Mendelian randomization, Meta analysis, GWAS, R, Python,
  common wet-lab methods, cohort/RCT work and medical literature retrieval.
- Users explicitly choose whether they merely know a method, can use it under
  supervision, can use it independently or can optimize/teach it. Unselected
  candidates do not appear in the final resume.
- Confirmed capabilities are stored in `resume-document-v1` with evidence IDs
  and are rendered in the top-level capability section of every resume layout.

### Verification

- Extended the schema contract with traceable `capability_profile` items.
- All 48 Python tests passed; JavaScript syntax and whitespace checks passed.
- Browser-tested a synthetic resume containing MR, Meta analysis, R, cell
  culture, qPCR, Western blot and PubMed. Confirmed MR, Meta analysis and qPCR
  appeared in the structured preview with the chosen proficiency levels.

## 2026-08-21 — resume-to-market translation foundation

### Product decision

- Started the job-capability translator as a deterministic, evidence-first
  service rather than a free-form prompt. It accepts a formal resume document
  and target JD, maps confirmed capability categories to their market value and
  recommends a resume placement.
- The service excludes a capability if any cited evidence is not marked
  `user_confirmed`. It does not generate a new accomplishment or increase a
  responsibility level.

### Verification

- Added direct tests for confirmed-evidence filtering and invalid inputs.
- All 50 Python tests passed.

## 2026-08-21 — target-specific medical capability translation

### Product decisions

- Added four initial target profiles: doctoral/recommendation, clinical
  research, MSL/medical affairs and health data/health technology.
- The same confirmed capability now receives a profile-specific market value
  and recommended placement. For example, a research method can be presented
  as research depth for doctoral applications or evidence interpretation for
  medical affairs.
- Added a browser-facing translator card. It requires the user to first save a
  structured resume and confirm capability proficiency, then shows only
  traceable recommendations and evidence-backed rationale.

### Verification

- Added target-profile translation tests for the same confirmed capability.
- All 51 Python tests passed; JavaScript syntax and whitespace checks passed.

## 2026-08-22 — standalone local release repository and Skill Lite

### Release packaging

- Synced the shared repository's `experience-compiler-v1` release source into
  the standalone `medical-resume-agent` repository while preserving the prior
  standalone history on a backup branch.
- Added `start-local.ps1` as the documented Windows local entry point. It
  checks for Python, installs the optional resume-extraction dependencies on a
  first run, and starts the local Flask service without requiring a model key.
- Rewrote Chinese and English READMEs around the public Beta scope: a local,
  evidence-bound medical experience compiler rather than a promise of arbitrary
  resume parsing or job outcomes.

### Skill Lite

- Added `skill-lite/medical-resume-skill`, a companion workflow for Codex or
  Claude users. It keeps methods, tools, wet-lab techniques, clinical research
  operations, evidence resources, roles, and deliverables as separate fact
  categories.
- The Skill requires fact confirmation before target-specific composition and
  ships four target-path references plus explicit anti-fabrication rules.
- Skill Lite is a prompt/workflow companion only; it does not claim to replace
  the web application's deterministic Claim Gate or audit ledger.
