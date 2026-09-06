> **历史原件 / archived 2026-09-06。** 原路径：`docs/llm-first-conversation-poc.md`；归档前最后提交日期：2026-09-05。原文版本：[Git 85701b51](https://github.com/melody-yu112358/medical-resume-agent/blob/85701b516f5889412e9791391c4dedcb2d7b0b38/docs/llm-first-conversation-poc.md)。当前承接入口：[有效说明](../../README.md)。原有日期、数量、计划、验证与结论保留当时语境，不代表当前库存或本次重新验收；归档不改变 legacy 规则。

# LLM-first conversation planning PoC

Each ordinary chat turn can enter through `ConversationModelGateway.plan_turn`.
The model receives a bounded session summary (stage, recent user messages,
draft facts, pending activity summaries, selected role packs, and gate states)
and returns a `ConversationTurnPlan`:

```json
{
  "assistant_message": "...",
  "proposed_actions": [{"type": "propose_fact_update", "evidence_quote": "..."}],
  "needs_user_reply": true
}
```

The model has no state-write capability. The PoC accepts only these action
types: `propose_fact_update`, `update_activity_responsibility`,
`select_role_packs`, `request_rewrite`, and `request_confirmation`.

`ResumeConversationAgent` validates every action against the current state and
the current user text before delegating to existing services. Fact proposals
require a verbatim evidence quote and deterministic extraction; responsibility
proposals require an existing pending activity and a verbatim quote; role packs
are an allow-list; and rewrites still use the existing candidate-claim plus
ClaimGate path. An answer-only plan never changes state.

If there is no model, invalid JSON, an empty plan, or an invalid proposed
action, the existing deterministic routing remains the fallback. This PoC does
not remove ConfirmationGate, canonical experience, evidence records, or
ClaimGate. The next phase can migrate remaining legacy intent branches only
after turn-plan evaluation data shows safe coverage.
