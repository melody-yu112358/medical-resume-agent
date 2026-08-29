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
