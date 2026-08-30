# Bounded LLM integration

## Role of the model

The model is a language explanation layer after deterministic comparison. It
does not select careers, calculate evidence coverage, apply hard constraints,
change ranking, retrieve salary information, or create personal evidence.

The server first runs:

```text
structured profile
  -> sourced career cards
  -> deterministic capability coverage and constraints
  -> at most three career hypotheses
  -> bounded model explanation
  -> output quality gate
```

The model receives only the stored comparison result. It must cite at least one
profile `evidence_id` for each hypothesis. The quality gate rejects empty or
short answers, fixed-fit language, invented percentages, missing careers,
missing evidence references, and added URLs.

This gate reduces common failure modes but does not prove that every sentence
is correct. Model text remains generated wording and must be shown separately
from deterministic data and source-backed career claims.

The model has a second bounded role before comparison: proposing an unverified
profile draft from consented experience text. It may attach approved capability
labels only to verbatim source quotes. Code rejects quotes not found in the
input, and the user must confirm each evidence item before comparison.

## Local configuration

The recommended Windows flow stores the API key in a user environment variable
and keeps all non-secret settings in versioned JSON:

```powershell
.\set-llm-key.ps1
.\start-with-llm.ps1
```

The hidden prompt writes only `MEDICAL_RESUME_LLM_API_KEY` to the current-user
environment. `config/llm.runtime.json` contains the provider label, base URL,
model and timeout, but never the key. The launcher maps these values to
process-only `LLM_*` variables used by the existing application gateways.

Legacy `.env` loading remains supported for local development. `.env` is
ignored by Git and must never be committed.

The adapter uses the OpenAI-compatible `POST /chat/completions` shape and can
also target another compatible provider by changing the three values. The
application never returns or logs the API key.

DeepSeek V4 enables thinking mode by default. This explanation-only endpoint
explicitly disables thinking for the official `api.deepseek.com` host so the
token budget is used for the final bounded explanation rather than hidden
reasoning. Other compatible hosts receive only the generic request fields.

Validate the JSON and environment-variable configuration without making a
model or health request:

```powershell
.\start-with-llm.ps1 -CheckOnly
```

Then open `http://127.0.0.1:5000/`. `start-local.ps1` remains available for a
model-free local preview. The health endpoint reports configuration status and
non-secret model metadata; it never returns the API key.

## API boundary

- `POST /api/career-comparisons` is deterministic and model-free.
- `POST /api/career-explanations` reruns the same deterministic comparison,
  sends the bounded result to the model, validates the output, and returns both
  objects separately.
- `POST /api/profile-drafts` proposes grounded, unverified evidence and does not
  persist the request or response.
- A model network failure or rejected output returns an error; the server does
  not replace it with invented text.

## Current limitations

- The original integration page still uses three source-controlled synthetic
  profiles; the separate intake page can submit consented text to the locally
  configured model provider.
- Transient intake has no account, autosave, database, retention workflow or
  deletion API. It is a local validation page, not a production privacy model.
- The model cannot call arbitrary tools or modify profiles and career cards.
- A future agent loop may expose the four approved domain tools only after
  authentication, consent, audit logging, and tool-level tests are defined.
