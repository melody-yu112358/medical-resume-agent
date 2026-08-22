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

Copy `.env.example` to `.env` and fill in a personal API key. `.env` is ignored
by Git and must never be committed.

DeepSeek example:

```text
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=<your key>
LLM_MODEL=deepseek-v4-flash
```

The adapter uses the OpenAI-compatible `POST /chat/completions` shape and can
also target another compatible provider by changing the three values. The
application never returns or logs the API key.

DeepSeek V4 enables thinking mode by default. This explanation-only endpoint
explicitly disables thinking for the official `api.deepseek.com` host so the
token budget is used for the final bounded explanation rather than hidden
reasoning. Other compatible hosts receive only the generic request fields.

Run the local server:

```powershell
python -m pip install -e .
python -m medical_career_agent.api
```

Then open `http://127.0.0.1:5000/demo/`. Deterministic comparison works without
an API key. The model explanation button returns a clear configuration error
until all three environment values are present.

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
