#!/usr/bin/env python3
"""Portable invariants for Generalist-transition Beta assets.

This intentionally validates only packaged structure, fact references, negative
rules, and fixture-level ownership boundaries. It is not an Agent Claim Gate and
does not attempt to judge unconstrained natural-language model output.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_ROOT = SKILL_ROOT / "references"
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(cases: dict, contract: dict, modules: dict, rules: dict) -> list[str]:
    failures: list[str] = []
    module_ids = {module["id"] for module in modules["modules"]}
    valid_statuses = set(contract["mapping"]["statuses"])
    families = {"product", "operations", "consulting", "heor_market_access", "commercial_business_analytics"}
    expected_scenarios = {"reasonable_transfer", "partial_match", "overclaim"}
    cases_by_family: dict[str, set[str]] = {family: set() for family in families}

    for case in cases["cases"]:
        case_id = case["case_id"]
        family = case.get("target_family")
        scenario = case.get("scenario")
        if family not in families:
            failures.append(f"{case_id}: unknown target family")
        else:
            cases_by_family[family].add(scenario)
        if scenario not in expected_scenarios:
            failures.append(f"{case_id}: invalid scenario")

        jd = case["jd_snapshot"]
        for field in contract["jd_snapshot"]["required_fields"]:
            if field not in jd:
                failures.append(f"{case_id}: JD snapshot missing {field}")
        if jd.get("source_type") not in contract["jd_snapshot"]["source_types"]:
            failures.append(f"{case_id}: invalid JD source type")
        if jd.get("retrieval_status") not in contract["jd_snapshot"]["retrieval_statuses"]:
            failures.append(f"{case_id}: invalid retrieval status")
        if not DIGEST_RE.fullmatch(jd.get("source_digest_sha256", "")):
            failures.append(f"{case_id}: JD source digest is not SHA-256")
        if jd.get("source_type") == "url" and not jd.get("url"):
            failures.append(f"{case_id}: URL source missing URL")
        if jd.get("retrieval_status") == "retrieved" and not jd.get("retrieved_at"):
            failures.append(f"{case_id}: retrieved JD missing timestamp")

        mapping = case["mapping"]
        if mapping.get("status") not in valid_statuses:
            failures.append(f"{case_id}: invalid mapping status")
        invalid_modules = set(mapping.get("module_ids", [])) - module_ids
        if invalid_modules:
            failures.append(f"{case_id}: unknown modules {sorted(invalid_modules)}")
        refs = mapping.get("confirmed_fact_refs", [])
        known_facts = set(case.get("confirmed_facts", []))
        if not set(refs).issubset(known_facts):
            failures.append(f"{case_id}: mapping uses unknown fact reference")
        if mapping["status"] in contract["mapping"]["fact_refs_required_for"] and not refs:
            failures.append(f"{case_id}: evidence mapping has no fact reference")
        if mapping["status"] in contract["mapping"]["fact_refs_forbidden_for"] and refs:
            failures.append(f"{case_id}: explicit gap cannot cite personal facts")

        safety = case["claim_safety"]
        if safety.get("expected_outcome") not in contract["claim_safety"]["outcomes"]:
            failures.append(f"{case_id}: invalid claim-safety outcome")
        active_rules = [
            rule for rule in rules["rules"]
            if not set(rule["missing_evidence"]) & set(case.get("evidence_flags", []))
        ]
        detected = {
            phrase
            for rule in active_rules
            for phrase in rule["prohibited_claims"]
            if phrase.lower() in safety["candidate_text"].lower()
        }
        if safety["expected_outcome"] == "allowed" and detected:
            failures.append(f"{case_id}: allowed text contains prohibited claim {sorted(detected)}")
        if safety["expected_outcome"] == "revision_required" and not detected:
            failures.append(f"{case_id}: unsafe fixture does not trigger a negative rule")
        if safety.get("ownership_invariant") == "participated_not_owned" and safety["expected_outcome"] == "allowed":
            unsafe_ownership = {"主导", "独立负责", "牵头", "owned", "led", "drove"}
            found = [word for word in unsafe_ownership if word.lower() in safety["candidate_text"].lower()]
            if found:
                failures.append(f"{case_id}: participation wording upgrades ownership {found}")

    for family, scenarios in cases_by_family.items():
        if scenarios != expected_scenarios:
            failures.append(f"{family}: expected three scenarios, got {sorted(scenarios)}")
    if len(cases["cases"]) != 15:
        failures.append(f"expected 15 cases, got {len(cases['cases'])}")
    return failures


def validate_boundary_cases(cases: dict, rules: dict) -> list[str]:
    failures: list[str] = []
    rules_by_id = {rule["id"]: rule for rule in rules["rules"]}
    for case in cases["cases"]:
        rule = rules_by_id.get(case["rule_id"])
        if rule is None:
            failures.append(f"{case['case_id']}: unknown rule")
            continue
        active = not set(rule["missing_evidence"]) & set(case.get("evidence_flags", []))
        detected = [
            phrase for phrase in rule["prohibited_claims"]
            if phrase.lower() in case["candidate_text"].lower()
        ]
        if case["expected_outcome"] == "allowed" and active and detected:
            failures.append(f"{case['case_id']}: allowed wording triggers {detected}")
        if case["expected_outcome"] == "revision_required" and (not active or not detected):
            failures.append(f"{case['case_id']}: expected prohibited claim was not detected")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=REFERENCE_ROOT / "generalist-beta-eval-cases.json")
    parser.add_argument("--contract", type=Path, default=REFERENCE_ROOT / "generalist-beta-contract.json")
    parser.add_argument("--modules", type=Path, default=REFERENCE_ROOT / "transferable-capability-modules.json")
    parser.add_argument("--rules", type=Path, default=REFERENCE_ROOT / "generalist-beta-negative-mapping-rules.json")
    parser.add_argument("--boundary-cases", type=Path)
    args = parser.parse_args()
    rules = load_json(args.rules)
    failures = validate(load_json(args.cases), load_json(args.contract), load_json(args.modules), rules)
    if args.boundary_cases:
        failures.extend(validate_boundary_cases(load_json(args.boundary_cases), rules))
    if failures:
        print("generalist Beta invariant validation failed:")
        print("\n".join(failures))
        return 1
    suffix = " plus boundary cases" if args.boundary_cases else ""
    print(f"generalist Beta invariant validation passed: 15 cases{suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
