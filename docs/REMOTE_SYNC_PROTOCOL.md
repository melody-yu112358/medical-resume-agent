# Remote sync recovery protocol

This protocol distinguishes a completed, tested local phase from a delay in
GitHub synchronization. A connection timeout, reset, or unavailable GitHub
service is a **remote sync delay**; it is not evidence that local work or
tests failed.

## Local-first execution

For every change phase:

1. Complete the scoped code or documentation work locally.
2. Run the applicable tests.
3. After tests pass, create a clear local commit.
4. Record the branch name, local commit SHA, base branch, intended PR target,
   intended PR title and body, and tests passed.

Do not roll back a tested local commit, create a replacement branch, or alter
product code solely because GitHub cannot be reached.

## Required phase status

Every phase report must include exactly one `execution_status`:

- `completed_local`
- `awaiting_remote_sync`
- `pr_open`
- `review_pending`
- `changes_requested`
- `ci_failed`
- `ready_for_human_approval`

Use `ci_failed` only for a reported CI failure, not for a connection problem.

## Awaiting remote sync

After a push or PR-creation failure, set the phase to
`awaiting_remote_sync`. Preserve the existing local work and record:

- branch name;
- local commit SHA;
- base branch;
- intended PR title and body;
- tests passed;
- last push or PR error; and
- timestamp.

The record may be a durable local handoff record or the task's final report;
it must not contain secrets, tokens, or local credentials.

## Bounded retry and recovery

After the first remote failure, make at most two short additional remote
attempts. If they also fail, stop remote operations for that phase.

When connectivity is available in a later execution, do only the following:

1. verify the recorded local commit and clean branch;
2. push that existing branch without force; and
3. create or update the intended PR.

Do not reimplement the phase or create a duplicate branch or commit. If more
than one phase is `awaiting_remote_sync`, recover them in creation-time order,
and complete one push and PR before starting the next.

## Non-negotiable remote controls

- Never push directly to `main`.
- Never enable or perform automatic merge.
- Never force-push unless an identifiable human explicitly approves it.
- Never interpret a GitHub timeout as a code, test, or CI failure.
- After a push succeeds, set status to `pr_open` or `review_pending` and
  continue through PR, CI, Reviewer, Release Gate, and traceable human
  approval.
