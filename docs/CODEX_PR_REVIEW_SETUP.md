# Codex pull-request review setup

This repository's CI workflow can run on every pull request without a Codex integration. Codex review and `@codex` follow-up are account and repository integration features; this repository contains no GitHub App configuration, workflow token, or code-defined setting that can enable them.

## Current repository status

The repository contains GitHub Actions PR CI (`.github/workflows/tests.yml`) and the multi-agent handoff rules in `AGENTS.md`. Those files provide test results and review context, but they do **not** prove that Codex has been connected to this repository or that GitHub can route `@codex` mentions.

## Manual setup required

A repository administrator must complete these steps in the Codex/ChatGPT GitHub integration UI and GitHub:

1. Connect the GitHub account that owns or administers `melody-yu112358/medical-resume-agent` to Codex, then grant the Codex GitHub integration access to this repository.
2. If the integration offers repository selection, explicitly enable this repository; if it uses a GitHub App installation, install or approve that app for this repository.
3. In the Codex integration settings, enable pull-request code review and follow-up-by-mention only if those controls are available for the account or plan.
4. On GitHub, confirm the integration identity can read pull requests and commit contents and can write pull-request review comments. Do not grant write-to-contents, Actions secrets, or merge permissions merely for review.
5. Open a small test PR, request a Codex review through the enabled integration, then leave an `@codex` follow-up comment. Confirm that both the review and the reply appear on that PR.

If any control is unavailable, the repository can still use the CI workflow and manual Codex task handoffs. Record the unavailable control and do not represent automated review or `@codex` follow-up as enabled.

## Scope boundary

This document intentionally does not add a bot token, webhook, GitHub App manifest, secret, or merge automation. Those require an administrator's explicit authorization and should be handled in a separately scoped change.
