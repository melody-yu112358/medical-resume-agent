# Generalist-transition Beta

This opt-in route tests whether confirmed medical experience can be translated for a specific non-core job description without inventing target-role ownership. It does not create a fifth target, a Role Pack, or a fallback for the four established paths.

## Entry rule

Use the route only when the user explicitly requests a direction outside the four established paths and provides a concrete JD. The JD may be pasted text or a readable URL. A URL that cannot be retrieved is not a JD: ask the user to paste the contents instead of guessing from the link name.

## Records that must remain separate

```text
Confirmed fact card  → personal evidence eligible for wording
JD snapshot          → role requirements and terminology only
Evidence-to-JD map   → match level, limitations, and gaps
Claim-safety audit   → whether a proposed sentence is allowed
```

The JD snapshot includes source type, URL when applicable, retrieval time only when retrieval occurred, retrieval status, and a SHA-256 digest of the captured source. It must not be merged into the fact card.

## Required sequence

1. Confirm facts and responsibility boundaries.
2. Capture the JD snapshot.
3. Map confirmed facts through the transferable capability modules.
4. Show direct evidence, transferable evidence, partial matches, and explicit gaps.
5. Show prohibited claims separately from match status.
6. Ask the user to confirm the mapping.
7. Draft wording using only approved mappings.
8. Audit every draft sentence for fact and ownership safety.

## Mapping statuses

- `direct_evidence`: the confirmed fact directly covers the JD item at the evidenced scope.
- `transferable_evidence`: a confirmed underlying capability is relevant, but target-role context or ownership is not claimed.
- `partial_match`: some relevant evidence exists, but scope, tool, domain, stakeholder, or ownership evidence is incomplete.
- `explicit_gap`: no confirmed evidence supports the JD item.

These statuses answer "how does the evidence relate to this JD?" They do not answer whether a draft sentence is safe. Use `claim_safety` and `prohibited_claims` in the final audit for that question.

## Product-specific boundary

A clinical or research problem is not automatically a user need. Without confirmed interviews, requirements collection, user feedback, or comparable evidence, product translation may mention clinical/research problem framing, analytical reasoning, evidence-based prioritization support, and result communication only. It must not claim user research, user insights, PRD work, roadmap ownership, or product ownership.

## Candidate-facing Beta output

```markdown
### JD snapshot
- Source: pasted text / URL, retrieval status and digest

### Evidence-to-JD mapping
- Direct evidence: ...
- Transferable evidence: ...
- Partial match: ...
- Explicit gaps: ...

### Draft safety audit
- Allowed wording: ...
- Prohibited claims: ...
- Ownership boundary: ...

### Representative wording
- Conservative / Professional / High impact: same confirmed fact set
```
