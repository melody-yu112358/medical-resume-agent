# Standalone model conformance evaluation

This is a separate evaluation from the offline standalone invariant tests.

`scripts/validate_standalone_cases.py` is suitable for CI because it checks only the package's generated rules, fixtures, and deterministic validator. It does **not** call a model and therefore does not prove that a model will always preserve facts or responsibility boundaries.

Run a model-conformance evaluation only in a deliberately isolated copy of `medical-resume-skill`: no repository `src/`, `data/`, or Agent prompt/config may be present. For each role pack, supply confirmed facts plus a target request, then record the model output and review it against these criteria:

- no new methods, tools, metrics, outcomes, or responsibilities;
- participation is not rewritten as ownership, leadership, management, or independent delivery;
- role emphasis follows the bundled generated `role-packs.md` and `role-pack-rules.json`;
- forbidden claims for the selected pack are absent;
- all three expression tiers remain factual paraphrases of the same confirmed fact set.

Store the model name, model version, prompt, package `source_digest_sha256`, inputs, outputs, and reviewer decision for every run. Treat this as a release conformance gate when prompts or models change, not as an invariant CI test.

## Generalist-transition Beta

For the opt-in Beta route, run every case in `generalist-beta-model-conformance-cases.json` in the same isolated package. Use the paired fixture as the source of confirmed facts and JD requirements. Review factuality, ownership preservation, JD keyword alignment, gap honesty, transferable-capability quality, and unsupported-claim rate. Do not use keyword count as a success metric.

The model must keep JD-match status (`direct_evidence`, `transferable_evidence`, `partial_match`, `explicit_gap`) separate from the draft claim-safety audit. A JD can establish terminology and a gap; it can never establish personal product, client, commercial, stakeholder, or leadership ownership.
