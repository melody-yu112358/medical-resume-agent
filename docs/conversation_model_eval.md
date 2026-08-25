# Conversation model evaluation harness

This harness evaluates an installed OpenAI-compatible model through the existing
`OpenAICompatibleModelGateway` and `ModelGatewayConversationGateway`. It does
not add a model SDK or change production conversation behaviour.

## Run

Normal offline tests never contact a model:

```powershell
$env:PYTHONPATH='.'; pytest -q
```

For a real-model run, set all three variables in the current shell and run:

```powershell
$env:PYTHONPATH='.'
$env:LLM_BASE_URL='https://…/v1'
$env:LLM_API_KEY='…'
$env:LLM_MODEL='…'
python scripts/run_conversation_model_eval.py
```

Use `--limit 2` for a low-cost smoke run and `--output <path>` to choose a
local report path. Without all three variables, the command prints `SKIPPED`
and exits successfully. Reports default to `tmp/model-evals/`, which is ignored
by Git. The report contains only synthetic case text and normalized candidate
fields; it intentionally does not retain full provider responses or credentials.

## What is evaluated

For each case the report records the input, validated activity proposals,
evidence quote, semantic warnings, responsibility candidates, and each of the
three constrained-rewrite attempts. Rewrites run only after the model has
returned confirmable activity proposals and the deterministic confirmation,
composition, and ClaimGate steps have succeeded. Otherwise every tone is
recorded as `not_run` with its deterministic reason. This makes missing or
unsafe decomposition visible rather than manufacturing a canonical record for
the model.

`unsupported_or_invalid` is derived from ClaimGate not being `ready` or a
proposal validation failure. `responsibility_inflation` is derived from ClaimGate
checks that identify responsibility, ownership, scope, or project-role upgrades.
These are safety signals, not a substitute for review.

## Human scoring template

Score each dimension 1 (poor) to 5 (excellent), and record a short rationale:

| Dimension | Score | Reviewer note |
| --- | --- | --- |
| Fact fidelity |  | Are action, method, tool, and outcome claims supported by the input? |
| Responsibility fidelity |  | Do ownership, execution mode, and scope preserve the user's boundary? |
| Activity decomposition quality |  | Are distinct responsibilities split into useful atomic activities? |
| Conversation naturalness |  | Are clarifications understandable and appropriately cautious? |
| Rewrite quality |  | Does each tone improve phrasing while preserving the confirmed basis? |
| Overclaim risk |  | Does the output imply unsupported independence, ownership, scale, or outcome? |

Reviewers should separately flag a model proposal that is semantically plausible
but needs a user confirmation; that is not evidence that it may enter canonical
data.
