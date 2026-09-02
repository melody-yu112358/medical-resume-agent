from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
EVIDENCE_PATH = ROOT / "docs" / "research" / "role-validation" / "regulatory-medical-writing" / "candidate-evidence-v1.json"


def load_evidence():
    return json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))


def test_regulatory_medical_writing_qualifying_jds_are_traceable_and_reproducible():
    evidence = load_evidence()
    qualifying = [snapshot for snapshot in evidence["jd_snapshots"] if snapshot["qualifying"]]

    assert len(qualifying) >= 8
    assert len({snapshot["employer"] for snapshot in qualifying}) >= 5
    for snapshot in qualifying:
        assert snapshot["status"] != "search_extract_not_countable"
        assert snapshot["url"].startswith("https://")
        assert snapshot["retrieved_at"]
        assert snapshot["source_snapshot"]
        assert snapshot["source_digest"] == hashlib.sha256(
            snapshot["source_snapshot"].encode("utf-8")
        ).hexdigest()


def test_regulatory_medical_writing_keeps_senior_scope_and_negative_mappings_explicit():
    evidence = load_evidence()
    jd_dependent = "\n".join(evidence["jd_dependent_or_senior_scope"])
    prohibited_claims = "\n".join(
        rule["must_not_claim"] for rule in evidence["negative_mapping_rules"]
    )

    for boundary in ("submission", "client", "protocol/CSR", "regulatory strategy"):
        assert boundary in prohibited_claims
    for senior_boundary in ("strategy", "regulatory", "client", "management"):
        assert senior_boundary in jd_dependent

    rules = evidence["negative_mapping_rules"]
    assert len(rules) >= 4
    assert all(rule["if_evidence"] and rule["must_not_claim"] for rule in rules)


def test_regulatory_medical_writing_personas_and_cases_cover_multiple_jds():
    evidence = load_evidence()
    qualifying_ids = {snapshot["id"] for snapshot in evidence["jd_snapshots"] if snapshot["qualifying"]}
    persona_ids = {persona["id"] for persona in evidence["fixed_personas"]}
    matrix = evidence["persona_jd_exercise_matrix"]

    assert len(persona_ids) >= 8
    assert set(matrix) == persona_ids
    assert all(len(jd_ids) >= 3 and set(jd_ids) <= qualifying_ids for jd_ids in matrix.values())
    employers_by_jd = {
        snapshot["id"]: snapshot["employer"]
        for snapshot in evidence["jd_snapshots"]
        if snapshot["qualifying"]
    }
    assert all(len({employers_by_jd[jd_id] for jd_id in jd_ids}) >= 3 for jd_ids in matrix.values())
    assert {case["expected_mapping_class"] for case in evidence["eval_cases"]} == {
        "direct", "transferable", "partial", "gap"
    }
    assert evidence["graduation_precheck"]["status"].startswith("PASS — Candidate")
