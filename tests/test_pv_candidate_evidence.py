from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
EVIDENCE_PATH = ROOT / "docs" / "research" / "role-validation" / "pharmacovigilance" / "candidate-evidence-v1.json"


def test_pv_candidate_jd_snapshots_are_traceable_and_countable():
    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    snapshots = evidence["jd_snapshots"]

    assert len(snapshots) >= 8
    assert len({snapshot["employer"] for snapshot in snapshots}) >= 5
    for snapshot in snapshots:
        assert snapshot["status"] != "search_extract_not_countable"
        assert snapshot["url"].startswith("https://")
        assert snapshot["retrieved_at"]
        assert snapshot["source_snapshot"]
        assert snapshot["source_digest"] == hashlib.sha256(
            snapshot["source_snapshot"].encode("utf-8")
        ).hexdigest()


def test_pv_candidate_keeps_ownership_and_safety_negative_mappings():
    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    negative_mappings = "\n".join(evidence["negative_mappings"])

    for required_boundary in ("ICSR", "信号", "QPPV", "法规", "团队管理"):
        assert required_boundary in negative_mappings

    rules = evidence["negative_mapping_rules"]
    assert len(rules) >= 4
    assert all(rule["if_evidence"] and rule["must_not_claim"] for rule in rules)


def test_pv_personas_have_multi_jd_exercise_coverage():
    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    matrix = evidence["persona_jd_exercise_matrix"]
    persona_ids = {persona["id"] for persona in evidence["fixed_personas"]}
    snapshot_ids = {snapshot["id"] for snapshot in evidence["jd_snapshots"]}

    assert set(matrix) == persona_ids
    assert all(len(jd_ids) >= 3 for jd_ids in matrix.values())
    assert all(set(jd_ids) <= snapshot_ids for jd_ids in matrix.values())
