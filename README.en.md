# Unbounded Medical Resume Assistant

<p align="center">
  <a href="#run-locally"><img src="https://img.shields.io/badge/LOCAL-FIRST-245A47?style=flat-square" alt="Local first" /></a>
  <img src="https://img.shields.io/badge/EVIDENCE-BOUND-5E8570?style=flat-square" alt="Evidence bound" />
  <img src="https://img.shields.io/badge/205-TESTS-8BAA97?style=flat-square" alt="205 tests" />
  <img src="https://img.shields.io/badge/MEDICAL-CAREER-244638?style=flat-square" alt="Medical career" />
</p>

<p align="center"><a href="README.md">简体中文</a> · <b>English</b> · <a href="skill-lite/README.md">Skill Lite</a></p>

A local medical experience compiler for medical students preparing academic applications and medical-sector roles.

The user submits one experience, reviews the extracted facts, and selects a target direction. The application then drafts editable resume bullets and shows the confirmed information that supports them.

It is useful when a broad statement such as “participated in research” or “assisted with data analysis” needs to be separated into research object, method, tool, personal role, and deliverable before deciding what belongs in a resume.

> Real experience → confirmed research object, method, tool, role, and deliverable → transferable capability → value expression for a target direction

| What you provide | What the system does | What you receive |
| --- | --- | --- |
| A real medical experience | Extracts facts, asks about missing information, and waits for confirmation | Candidate bullets for a chosen target path |
| An experience containing methods, tools, or laboratory techniques | Separates research methods such as MR/Meta, analytical tools such as R/Python, laboratory techniques such as qPCR/WB, and retrieval resources such as PubMed/Embase | An explainable capability structure rather than keyword stuffing |
| A target direction | Adjusts emphasis without changing the underlying experience | Traceable, editable, reviewable material |

## Quick start

```powershell
.\start-local.ps1
```

Then open `http://127.0.0.1:5000/demo/experience-compiler/index.html`. For a first run, load the included de-identified Meta-analysis example. See [Run locally](#run-locally) for full setup instructions.

## Intended use

Medical research and clinical experience often combine a research question, methods, software tools, laboratory techniques, and operational work. Broad statements such as “participated in research”, “conducted literature retrieval”, or “assisted with data analysis” make it difficult for a reader to identify the work completed or the boundary of responsibility.

The application organizes raw experience into confirmable facts: study design, analytical method, tools, laboratory techniques, clinical-research operations, personal role, data or literature sources, and deliverables. It drafts target-specific candidate bullets only after the user has reviewed those facts.

## Initial medical capability taxonomy

The project currently uses the following categories to organize medical experience. They support fact confirmation and drafting decisions; a keyword alone does not establish proficiency.

1. **Study design and methods**: cohort studies, RCTs, Meta-analysis, Mendelian randomization (MR), GWAS, bioinformatics, and machine learning.
2. **Data and tools**: R, Python, SPSS, SQL, data cleaning, statistical analysis, and visualization.
3. **Clinical-research design and operations**: inclusion and exclusion criteria, follow-up, CRFs, ethics, GCP, real-world research, and data quality control.
4. **Laboratory techniques**: cell culture, qPCR, Western Blot, flow cytometry, ELISA, and animal studies.
5. **Medical evidence and information**: PubMed, Embase, and Cochrane searching, guideline interpretation, evidence grading, and medical writing.

## Workflow

1. Enter a real medical experience, or load the included de-identified Meta-analysis example.
2. Review extracted candidate facts and up to three clarifying questions.
3. Confirm, edit, or reject facts. Unconfirmed information is never silently promoted into an achievement.
4. Select a target direction and generate one to three candidate resume bullets.
5. Review evidence links, risk notices, and audit records before copying or exporting the result.

The current release provides four target directions:

- **Doctoral / academic applications**: research question, methodological depth, and research potential.
- **Clinical research**: study design, clinical context, execution, and collaboration.
- **Medical affairs / MSL**: evidence interpretation, disease-area knowledge, and medical-information translation.
- **Health AI / medical data**: data handling, analytical framing, and communication of findings.

## Rules and known limitations

- Candidate bullets use user-confirmed facts only. The application does not turn “participated” into “led”, or add unstated numbers, methods, tools, or outcomes.
- The taxonomy explains an experience; it does not infer proficiency from a keyword. R/Python, MR/Meta, qPCR/WB, and PubMed/Embase belong to different categories and require user confirmation in context.
- File extraction works best with ordinary DOCX, TXT, Markdown, and text-based PDFs. Text order may be unreliable in two-column, table-heavy, or scanned PDFs and should be corrected on the confirmation screen.
- The local Beta does not provide employment, salary, or role-fit conclusions, and it does not reproduce arbitrary resume layouts pixel-for-pixel.

## Run locally

### Requirements

- Windows 10/11 (the first-launch script targets Windows)
- Python 3.11+
- Network access only for the first dependency installation; the web page and experience processing run locally afterwards

### Quick start

1. Download and unzip this repository, or run:

   ```powershell
   git clone https://github.com/melody-yu112358/medical-resume-agent.git
   cd medical-resume-agent
   ```

2. Open PowerShell in the project directory and run:

   ```powershell
   .\start-local.ps1
   ```

   If PowerShell blocks the script, run this in the current shell only:

   ```powershell
   Set-ExecutionPolicy -Scope Process Bypass
   .\start-local.ps1
   ```

3. When the server starts, open:

   ```text
   http://127.0.0.1:5000/demo/experience-compiler/index.html
   ```

4. Return to PowerShell and press `Ctrl + C` to stop the local service.

### Optional model-assisted wording

The deterministic fact extraction, confirmation, target-specific bullet generation, and audit path work without a model.

To enable bounded wording optimization with an OpenAI-compatible model such as DeepSeek, create a local `.env` file:

```powershell
Copy-Item .env.example .env
```

Then follow the [model configuration guide](docs/LLM_INTEGRATION.md). Keep keys in local environment files only; never paste them into browser code, screenshots, or GitHub issues.

## Skill Lite for Codex/Claude users

The web interface is intended for users who do not want to configure an AI coding tool. This repository also includes a lightweight workflow Skill for deeper experience interviewing in Codex or Claude:

- [Skill Lite guide](skill-lite/README.md)
- [Skill entrypoint](skill-lite/medical-resume-skill/SKILL.md)

Skill Lite follows the same method—extract facts, confirm facts, then translate for a target direction—but it is a prompt/workflow package. It does not replace the web app's deterministic Claim Gate or audit trail.

## Verify

```powershell
python -m pip install -e ".[resume_extract,dev,schema_validation]"
python -m pytest -q
```

The shared release source contains 205 unit, API, and end-to-end tests. Before a public test, also complete a browser smoke test: load the example, extract facts, confirm them, select a direction, generate bullets, review evidence, and export.

## Repository map

```text
demo/experience-compiler/  browser experience compiler
src/medical_career_agent/  extraction, confirmation, composition, Claim Gate, and ledger
schemas/                   canonical experience, role pack, and bullet claim contracts
data/role-packs/           four target-specific expression strategies
skill-lite/                lightweight workflow package for Codex/Claude users
docs/                      architecture, boundaries, model setup, and acceptance material
tests/                     synthetic, API, and boundary tests
```

## Feedback

We welcome de-identified testing from medical students, researchers, clinical-research practitioners, MSLs, and medical-data practitioners. Do not submit real names, contact information, clinical records, participant information, unpublished research data, or keys.
