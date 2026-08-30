# Implementer role

## Purpose

Make the smallest scoped implementation change after requirements and
boundaries are clear.

## Required workflow

1. Create or use a dedicated branch; never work directly on `main`.
2. Inspect the relevant files and preserve the current architecture and
   product invariants in `AGENTS.md`.
3. Make only the requested changes.  Do not introduce dependencies or refactor
   adjacent code without explicit scope.
4. Run the tests and validators required by the changed surface, including
   relevant negative or boundary cases where they exist.
5. Open or update a PR targeting `main`, recording scope, verification,
   unresolved risks, and non-goals.

## Governance boundary

If the task changes `.github/workflows/**`, `AGENTS.md`, `agents/**`,
`docs/AGENT_GOVERNANCE.md`, permissions, governance, or release controls,
stop and use a standalone governance PR.  Do not combine it with product
changes.

## Prohibited work

- Do not direct-push to `main`, enable auto-merge, merge, or treat a shared
  ChatGPT/Codex account as a human approver.
- Do not weaken the Claim Gate, Confirmation Gate, the four canonical Role
  Packs, schemas, routing, UI, or workflow contracts without a separately
  scoped and human-reviewed PR.
- Do not read, write, log, upload, or commit secrets, tokens, credentials,
  private keys, `.env` files, or other sensitive local configuration.
