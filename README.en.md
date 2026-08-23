# Unbounded Medical Resume Assistant

[简体中文](README.md) · [Skill Lite](skill-lite/README.md)

<img src="assets/brand/hero.svg" alt="Unbounded Medical Resume Assistant" width="100%" />

This repository contains a local medical-resume assistant. Its main interface, the Medical Experience Compiler, accepts one experience at a time, lets the user review extracted facts, and drafts editable resume bullets for a selected career direction.

It is intended for medical students and early-career applicants preparing doctoral applications, clinical-research roles, medical-affairs roles, or health-data roles. The project is designed to clarify existing experience, not to fill gaps with invented achievements.

<img src="assets/brand/experience-flow.svg" alt="Experience workflow: experience, fact confirmation, target selection, and resume bullets" width="100%" />

## What is available

- Enter a medical experience or load the bundled de-identified Meta-analysis example.
- Extract candidate facts about methods, tools, laboratory techniques, research operations, personal responsibility, and deliverables.
- Ask up to three focused questions when key information is missing.
- Confirm, edit, or reject each candidate fact.
- Draft resume bullets for four target directions, with supporting facts and risk notices.
- Copy or export the result.
- Use the included Skill Lite package in Codex for the same fact-confirmation workflow.

The current role packs are:

| Direction | What the draft emphasizes |
| --- | --- |
| Doctoral / academic applications | Research question, methodological grounding, and research potential |
| Clinical research | Study design, clinical-research operations, data, and collaboration |
| Medical affairs / MSL | Evidence interpretation, disease-area information, and medical communication |
| Health AI / medical data | Data handling, analytical framing, and presentation of findings |

A role pack changes the emphasis of a confirmed experience; it does not change the underlying facts.

## Run locally

Open PowerShell in the project directory and run:

```powershell
.\start-local.ps1
```

When the server is ready, open:

```text
http://127.0.0.1:5000/demo/experience-compiler/index.html
```

For a first run, load the de-identified Meta-analysis example from the page, then complete fact confirmation, direction selection, and bullet generation.

### First-time setup

Windows 10/11 and Python 3.11 or newer are required. The startup script installs missing Python packages on first use; subsequent processing runs locally.

To download the repository first:

```powershell
git clone https://github.com/melody-yu112358/medical-resume-agent.git
cd medical-resume-agent
.\start-local.ps1
```

If PowerShell blocks the script, run the following in the current shell only:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\start-local.ps1
```

Press `Ctrl + C` in PowerShell when you are finished to stop the local server.

## Evidence and wording rules

The project keeps tools, methods, techniques, and research resources separate. R/Python are software tools; MR/Meta are research methods; qPCR/WB are experimental techniques; PubMed/Embase are literature-retrieval resources. These categories carry different meaning in a resume and should not be collapsed into a generic “research skills” label.

Before a stronger statement is drafted, the user confirms their contribution and any verifiable deliverables. Missing evidence remains a risk notice or becomes a question. The application does not automatically add claims such as “led”, “independently completed”, numerical results, or unstated methods.

File extraction currently works best with ordinary DOCX, TXT, Markdown, and text-based PDFs. Text order may be unreliable in two-column, table-heavy, or scanned PDFs; review the extracted content before proceeding. The project does not promise role fit, employment outcomes, or pixel-perfect reproduction of arbitrary resume layouts.

## Optional model configuration

Fact extraction, confirmation, target-specific drafting, and the audit path work without a model. To enable constrained wording assistance from an OpenAI-compatible model such as DeepSeek, create a local configuration file:

```powershell
Copy-Item .env.example .env
```

Then follow the [model configuration guide](docs/LLM_INTEGRATION.md). Keep keys in the local `.env` file; do not commit them or include them in browser code, screenshots, or issues.

## Skill Lite

`skill-lite/` contains a lightweight workflow package for Codex users who prefer to work through an experience in a conversation. It follows the same order: identify facts, confirm them, and then draft for a target direction.

See the [Skill Lite guide](skill-lite/README.md) for installation and usage. Skill Lite is a prompt and workflow package; it does not replace the web application's fact confirmation, Claim Gate, or audit record.

## Verification

```powershell
python -m pip install -e ".[resume_extract,dev,schema_validation]"
python -m pytest -q
```

The release source currently includes 205 unit, API, and end-to-end tests. Before a demo or release, also run through the browser flow: load the example, confirm facts, choose a direction, generate bullets, review the supporting information, and export the result.

## Repository layout

```text
demo/experience-compiler/  browser interface for the experience compiler
src/medical_career_agent/  extraction, confirmation, drafting, Claim Gate, and ledger services
schemas/                   Canonical Experience, Role Pack, and Bullet Claim contracts
data/role-packs/           drafting strategies for the four directions
skill-lite/                Codex Skill Lite
docs/                      architecture, boundaries, model configuration, and acceptance material
tests/                     synthetic, API, and boundary tests
```

## Feedback and privacy

De-identified test cases are welcome. Do not submit real names, contact details, medical records, participant information, unpublished research data, or keys.
