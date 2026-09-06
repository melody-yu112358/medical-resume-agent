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

## PR review integration setup

The following integration setup guidance is carried forward from CODEX_PR_REVIEW_SETUP.md. It does not change any approval, permission, role, branch, CI or merge requirement above. The [historical original](archive/governance/CODEX_PR_REVIEW_SETUP.md) retains the prior text; future setup documentation belongs in this section. Availability must be verified in the relevant UI, not inferred from the existence of this guide.

This repository's CI workflow can run on every pull request without a Codex integration. Codex review and `@codex` follow-up are account and repository integration features; this repository contains no GitHub App configuration, workflow token, or code-defined setting that can enable them.

### Current repository status

The repository contains GitHub Actions PR CI (`.github/workflows/tests.yml`) and the multi-agent handoff rules in `AGENTS.md`. Those files provide test results and review context, but they do **not** prove that Codex has been connected to this repository or that GitHub can route `@codex` mentions.

### Manual setup required

A repository administrator must complete these steps in the Codex/ChatGPT GitHub integration UI and GitHub:

1. Connect the GitHub account that owns or administers `melody-yu112358/medical-resume-agent` to Codex, then grant the Codex GitHub integration access to this repository.
2. If the integration offers repository selection, explicitly enable this repository; if it uses a GitHub App installation, install or approve that app for this repository.
3. In the Codex integration settings, enable pull-request code review and follow-up-by-mention only if those controls are available for the account or plan.
4. On GitHub, confirm the integration identity can read pull requests and commit contents and can write pull-request review comments. Do not grant write-to-contents, Actions secrets, or merge permissions merely for review.
5. Open a small test PR, request a Codex review through the enabled integration, then leave an `@codex` follow-up comment. Confirm that both the review and the reply appear on that PR.

If any control is unavailable, the repository can still use the CI workflow and manual Codex task handoffs. Record the unavailable control and do not represent automated review or `@codex` follow-up as enabled.

### Scope boundary

This document intentionally does not add a bot token, webhook, GitHub App manifest, secret, or merge automation. Those require an administrator's explicit authorization and should be handled in a separately scoped change.
