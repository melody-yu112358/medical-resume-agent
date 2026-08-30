# Agent governance and shared-account safety

## Purpose and scope

This policy governs automated or AI-assisted work in this repository.  It is
designed for an environment in which a ChatGPT/Codex account may be shared by
multiple people, including GitHub Writers.  It changes collaboration controls
only; it does not change canonical Role Pack semantics, workflow targets,
Claim Gate, Confirmation Gate, routing, UI, schemas, or product semantics.
Role Pack lifecycle and graduation criteria are defined only in
[ROLE_PACK_GRADUATION.md](ROLE_PACK_GRADUATION.md).

## Enforced by repository policy

- All agent work uses a dedicated branch and a PR to `main`; agents must not
  direct-push to `main`.
- Auto-merge is prohibited.  A traceable human GitHub account must make the
  final approval and merge decision.
- Researcher is report-only; Reviewer and Release Gate are read-only;
  Implementer may change scoped code only on a dedicated branch.
- Release Gate may issue only `PASS — merge recommended` or `FAIL — do not
  merge`.  It cannot approve or merge.
- Governance-sensitive files must be isolated in a governance-only PR:
  `.github/workflows/**`, `AGENTS.md`, `agents/**`, this document, and files
  affecting permissions, governance, or release controls.
- Secrets, tokens, private keys, credentials, `.env` files, and sensitive
  local configuration must not be read, written, logged, uploaded, or
  committed.

The authoritative role instructions are `AGENTS.md` and `agents/`.

## Human approval model

A shared ChatGPT/Codex session is not a trusted person and cannot satisfy a
required review or approval.  Key approval must come from an identifiable
human GitHub account with an auditable PR review.  GitHub Writer access alone
does not grant an agent authority to merge or alter governance.

## GitHub owner setup required

Repository files cannot themselves prevent a Writer, a compromised token, or
a shared account with GitHub credentials from pushing to `main`.  Before
treating this policy as technically enforced, a repository owner should use
the GitHub UI to configure and document the following settings in a separate
human-reviewed governance PR/decision:

1. Protect `main`: require pull requests before merging and block direct
   pushes, including for administrators unless an emergency policy says
   otherwise.
2. Require at least one approving review from a traceable human GitHub
   account; dismiss stale approvals when new commits are pushed.
3. Require the `pytest` status check from the existing test workflow (and any
   future agreed checks) before merge.  Do not enable new required checks
   until they have first run reliably on PRs.
4. Disable auto-merge for the repository, or restrict it so it cannot be used
   for agent-authored PRs.
5. Limit who can bypass branch protection and who can change Actions,
   repository settings, secrets, and access controls.  Use personal GitHub
   accounts and least-privilege tokens; do not share credentials.
6. Enable secret scanning and push protection where available, then document
   any organization-level exceptions separately.

These are deliberately not enabled by this PR: they are external repository
settings that can affect Writer collaborators and must be approved by the
owner through GitHub's UI.

## PR classification and handoff

Every PR must identify one class: `governance`, `research`, `implementation`,
or `release evidence`.  Governance PRs must contain only governance changes;
other PRs must not modify governance-sensitive paths.  The PR description
must include the scope, changed files, verification, unresolved risks, and
non-goals.  Review and Release Gate outputs are advisory records, not merge
authority.
