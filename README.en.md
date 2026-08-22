# Unbounded | Medical Resume Agent

**English** | [简体中文](README.md)

An evidence-based medical experience compiler that runs on your own computer, built for medical students preparing graduate-school applications and early-career job applications.

It does not simply make an experience sound stronger. It first asks the user to confirm the underlying facts, then turns the same medical experience into resume bullets that different target paths can understand and challenge.

> Real experience → method / tool / role / research object / deliverable → transferable capability → target-specific emphasis

## Why this project?

“Participated in research”, “conducted literature retrieval”, and “assisted with data analysis” rarely show what a candidate actually did or where their responsibility ends.

Unbounded separates an experience into confirmable facts: study design, analytical method, tools, wet-lab techniques, clinical-research operations, personal role, data or literature sources, and deliverables. Only after the user confirms those facts does it generate target-specific candidate bullets.

## Current workflow

1. Enter a real medical experience, or load the included de-identified Meta-analysis example.
2. Review extracted candidate facts and up to three clarifying questions.
3. Confirm, edit, or reject facts. Unconfirmed information is never silently promoted into an achievement.
4. Select a target direction and generate one to three candidate resume bullets.
5. Review evidence links, risk notices, and audit records before copying or exporting the result.

The launch Beta supports four directions:

- **Doctoral / academic applications**: research question, methodological depth, and research potential.
- **Clinical research**: study design, clinical context, execution, and collaboration.
- **Medical affairs / MSL**: evidence interpretation, disease-area knowledge, and medical-information translation.
- **Health AI / medical data**: data handling, analytical framing, and communication of findings.

## Truth boundaries

- It does not turn “participated” into “led”, or invent numbers, methods, tools, or outcomes.
- R/Python are tools; MR/Meta are methods; qPCR/WB are experimental techniques; PubMed/Embase are evidence-retrieval resources. They are not collapsed into a vague single “research skills” label.
- Strong claims must point back to user-confirmed facts and evidence. Missing information becomes a question, not a guess.
- The current Beta works best with ordinary DOCX, TXT, Markdown, and text-based PDFs. Complex two-column, table-heavy, or scanned PDFs may need correction on the confirmation screen.
- It does not promise employment, salary, role fit, or pixel-perfect reproduction of arbitrary resume layouts.

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
