# Build log

## 2026-08-20 — medical resume agent foundation

- Created a standalone medical resume project from the resume-specific parts of
  the larger medical-career-agent project. The original career exploration
  product remains separate.
- Added deterministic JD evidence matching, optional DeepSeek-compatible
  rewriting with source/number/responsibility checks, final-resume review, A4
  browser print preview, and three visual styles.
- Added purpose-specific flows: 保研/夏令营、考研复试、考博、医院/规培校招、医药健康行业校招、社招、通用简历.
- Each purpose has a different preview section order and a medical-specific
  checklist, for example English/research/mentor fit for applications and
  clinical rotations/certifications for hospital recruitment.
- Added an opt-in browser-local master evidence bank and named resume-version
  saving. Data is stored only in the active browser's localStorage; it is not
  sent to the backend, GitHub, or the model by the save action.
- Known limitation: version records currently store a generated-rewrite count,
  not per-suggestion accept/reject decisions. That is the next planned audit
  feature.

### Verification

- Python unit tests: 4 passed.
- `node --check demo/resume-beta/app.js` passed.
- `git diff --check` passed.

### Git status

- `2e73a7c feat: add purpose-specific resume flows and evidence bank` was
  committed locally; pushing from the terminal was blocked by the local
  GitHub network connection. GitHub Desktop is used for the user-authorized
  push.
