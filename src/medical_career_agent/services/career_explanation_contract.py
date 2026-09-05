"""Versioned, deterministic explanation semantics; no occupational scoring."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

QUERY_VERSION = "career-card-explanation-v2"
EXPLANATION_CLASSES = ("direct", "transferable", "partial", "gap", "unsupported")
CONDITIONAL_APPLICABILITY = {"jd_dependent", "senior_only", "ownership"}


def digest(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def interpreter_fingerprint() -> str:
    root = Path(__file__).parent
    return digest({name: hashlib.sha256((root / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
                   for name in ("career_card_explanation.py", "career_explanation_contract.py")})


def validate_schema(instance: Any, schema: dict[str, Any], name: str) -> None:
    errors = sorted(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(instance),
                    key=lambda error: str(list(error.path)))
    if errors:
        error = errors[0]
        # Report the field and validator, not the rejected evidence text.
        raise ValueError(f"invalid {name} at {'/'.join(map(str, error.path)) or '<root>'}: {error.validator}")


def validate_capabilities(profile: dict[str, Any], registry: dict[str, Any]) -> None:
    evidence = profile["evidence"]
    ids = [item["evidence_id"] for item in evidence]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate evidence_id")
    unknown = {code for item in evidence for code in item["capability_codes"]} - set(registry["capability_codes"])
    if unknown:
        raise ValueError(f"unknown capability code: {', '.join(sorted(unknown))}")
    if any(item["scope"] not in registry["scopes"] for item in evidence):
        raise ValueError("invalid profile scope")


def validate_rule(rule: dict[str, Any], registry: dict[str, Any]) -> None:
    unknown = set(rule["required_capability_codes"]) - set(registry["capability_codes"])
    if unknown:
        raise ValueError(f"unknown rule capability code: {', '.join(sorted(unknown))}")
    if set(rule["allowed_scopes"]) - set(registry["scopes"]):
        raise ValueError("invalid rule scope")
    classification, kind = rule["classification"], rule["claim"]["kind"]
    allowed = {
        "direct": {"transferable_direct", "stable_responsibility", "entry_requirement"},
        "transferable": {"transferable"},
        "partial": {"transferable_partial"},
        "gap": {"explicit_gap", "jd_dependent_scope", "entry_requirement"},
        "unsupported": {"transferable_direct", "transferable", "transferable_partial"},
    }
    if kind not in allowed[classification]:
        raise ValueError("invalid classification / claim kind combination")
    if (classification in {"direct", "gap"} or kind == "transferable_direct") and rule["evidence_relation"] != "direct":
        raise ValueError("direct requirement cannot use transferable relation")
    if kind in {"transferable", "transferable_partial"} and rule["evidence_relation"] != "transferable":
        raise ValueError("transferable claim cannot use direct relation")
    if kind == "transferable_partial" and rule["support_ceiling"] != "partial":
        raise ValueError("partial claim requires partial support ceiling")
    if rule["inference_boundary"] == "unsupported" and not rule.get("negative_mapping_text"):
        raise ValueError("unsupported boundary requires a Role Pack boundary reference")
    if classification == "unsupported" and rule["inference_boundary"] != "unsupported":
        raise ValueError("unsupported classification requires unsupported boundary")
    if kind in {"explicit_gap", "jd_dependent_scope"} and rule["applicability"] not in CONDITIONAL_APPLICABILITY:
        raise ValueError("JD-specific or ownership claim cannot be a default role gap")
    if rule["applicability"] == "role_core" and rule.get("negative_mapping_text"):
        raise ValueError("ownership boundary cannot be a default role gap")
    if classification in {"transferable", "partial", "unsupported"} and rule["applicability"] == "role_core":
        raise ValueError("optional evidence mapping cannot be a core requirement")


def project_labels(semantics: dict[str, str], *, assessable: bool, gap_applicable: bool) -> list[str]:
    """Nonexclusive display projection, independent of legacy authored classification."""
    relation = semantics["evidence_relation"]
    completeness = semantics["support_completeness"]
    boundary = semantics["inference_boundary"]
    labels = []
    if assessable:
        if relation == "direct" and completeness == "complete":
            labels.append("direct")
        if relation == "transferable" and completeness != "no_evidence":
            labels.append("transferable")
        if completeness == "partial":
            labels.append("partial")
        if completeness == "no_evidence" and gap_applicable and boundary == "supported":
            labels.append("gap")
    if boundary == "unsupported" and relation != "none":
        labels.append("unsupported")
    return labels


def evaluate(rule: dict[str, Any], evidence: list[dict[str, Any]], *,
             applicable_rule_keys: set[str] | None, seniority: str | None,
             jd_usable: bool = True) -> dict[str, Any]:
    scoped = [item for item in evidence if not rule["allowed_scopes"] or item["scope"] in rule["allowed_scopes"]]
    required = set(rule["required_capability_codes"])
    matched = [item for item in scoped if required.intersection(item["capability_codes"])]
    present = required.intersection(code for item in scoped for code in item["capability_codes"])
    absent = sorted(required - present)
    satisfied = bool(present) if rule["match_mode"] == "any_capability_present" else required.issubset(present)
    completeness = "no_evidence" if not present else (rule["support_ceiling"] if satisfied else "partial")
    status = "assessed"
    conditional = rule["applicability"] in CONDITIONAL_APPLICABILITY
    if conditional:
        if applicable_rule_keys is None:
            status = "not_assessable_without_jd"
        elif rule["rule_key"] not in applicable_rule_keys:
            status = "not_applicable_to_jd"
        elif rule["applicability"] == "senior_only" and seniority != "senior":
            status = "not_assessable_without_senior_jd"
        elif not jd_usable:
            status = "not_assessable_with_deprecated_jd"
    semantics = {
        "evidence_relation": rule["evidence_relation"] if present else "none",
        "support_completeness": completeness,
        "inference_boundary": "jd_dependent" if status != "assessed" else rule["inference_boundary"],
    }
    labels = project_labels(semantics, assessable=status == "assessed",
                            gap_applicable=rule["applicability"] == "role_core" or conditional)
    return {
        **semantics, "assessment_status": status, "display_labels": labels,
        "requirement_operator": "any_of" if rule["match_mode"] == "any_capability_present" else "all_of",
        "conditions_satisfied": satisfied,
        "matched_capability_codes": sorted(present), "missing_capability_codes": absent,
        # Unsatisfied alternatives are optional once any-of succeeds.
        "required_missing_capability_codes": [] if satisfied else absent,
        "profile_evidence_ids": sorted(item["evidence_id"] for item in matched),
        "capability_findings": [{"capability_code": code, "status": "present" if code in present else "no_evidence",
                                 "profile_evidence_ids": sorted(item["evidence_id"] for item in scoped if code in item["capability_codes"])}
                                for code in sorted(required)],
    }
