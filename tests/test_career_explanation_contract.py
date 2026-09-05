"""Explanation contract, provenance granularity and snapshot replay regressions."""
import copy
import json
import sqlite3

import pytest

from test_career_map_revisions import (
    ROOT, CDM, PACK, RULE, source_tree, build, read_json, write_json, rows, manifest,
)
from medical_career_agent.services.career_card_explanation import CareerCardExplanationService
from medical_career_agent.services.career_explanation_contract import project_labels, digest


@pytest.fixture()
def query_env(source_tree, tmp_path):
    db = tmp_path / "map.sqlite"
    build(source_tree, db)
    profile = read_json(ROOT / "data/career-map/career-card-explanation-test-profiles-v1.json")["profiles"][0]
    return source_tree, db, profile


def query(env, profile=None, **kwargs):
    _, db, original = env
    return CareerCardExplanationService(db).explain(profile=profile if profile is not None else original, role_pack=PACK, **kwargs)


def item(result, key=RULE):
    return next(value for value in result["items"] if value["rule_key"] == key)


def evidence_profile(profile, codes, scope="assigned_support"):
    changed = copy.deepcopy(profile)
    changed["evidence"] = [{"evidence_id": "test-evidence", "statement": "Explicit synthetic test evidence.",
                            "capability_codes": codes, "scope": scope, "evidence_status": "confirmed"}] if codes else []
    return changed


def context_for(env, key="cdm-lock-gap", **extra):
    snapshot_id = next(ref["jd_evidence_snapshot_id"] for ref in manifest(env[1])["jd_snapshot_revisions"] if ref["external_snapshot_id"] == "cdm-01")
    return {"jd_evidence_snapshot_ids": [snapshot_id], "applicable_rule_keys": [key], "confirmation_status": "confirmed", **extra}


@pytest.mark.parametrize("relation,completeness,boundary,assessable,gap_applicable,expected", [
    ("direct", "complete", "supported", True, True, ["direct"]),
    ("direct", "partial", "supported", True, True, ["partial"]),
    ("transferable", "complete", "supported", True, False, ["transferable"]),
    ("transferable", "partial", "supported", True, False, ["transferable", "partial"]),
    ("transferable", "partial", "unsupported", True, False, ["transferable", "partial", "unsupported"]),
    ("direct", "complete", "unsupported", True, False, ["direct", "unsupported"]),
    ("none", "no_evidence", "supported", True, True, ["gap"]),
    ("none", "no_evidence", "supported", True, False, []),
    ("none", "no_evidence", "jd_dependent", False, True, []),
])
def test_display_projection_is_nonexclusive(relation, completeness, boundary, assessable, gap_applicable, expected):
    assert project_labels({"evidence_relation": relation, "support_completeness": completeness,
                           "inference_boundary": boundary}, assessable=assessable, gap_applicable=gap_applicable) == expected


@pytest.mark.parametrize("codes,expected_missing", [
    (["crf_checking"], ["data_query_follow_up", "gcp_training"]),
    (["crf_checking", "data_query_follow_up"], ["gcp_training"]),
])
def test_partial_direct_all_of_is_retained_per_claim(query_env, codes, expected_missing):
    result = query(query_env, evidence_profile(query_env[2], codes))
    direct = item(result)
    assert direct["evidence_relation"] == "direct"
    assert direct["support_completeness"] == "partial"
    assert direct["display_labels"] == ["partial"]
    assert direct["required_missing_capability_codes"] == expected_missing
    assert direct["target_claim"]["claim_id"] == direct["provenance"]["career_card_claim_id"]
    assert not result["explanations"]["direct"]
    assert direct in result["explanations"]["partial"]
    assert "已确认的 CRF 核对、数据跟进和 GCP 事实" not in direct["explanation"]


def test_any_of_and_transferable_never_becomes_direct(query_env):
    result = query(query_env, evidence_profile(query_env[2], ["r_statistics"]))
    transfer = item(result, "cdm-quantitative-transferable")
    assert transfer["conditions_satisfied"] is True
    assert transfer["requirement_operator"] == "any_of"
    assert transfer["evidence_relation"] == "transferable"
    assert transfer["support_completeness"] == "complete"
    assert transfer["required_missing_capability_codes"] == []
    assert transfer["missing_capability_codes"] == ["laboratory_qc"]
    assert not result["explanations"]["direct"]


def test_transferable_partial_and_unsupported_on_same_item(query_env):
    result = query(query_env)
    boundary = item(result, "cdm-data-cleaning-boundary")
    assert (boundary["evidence_relation"], boundary["support_completeness"], boundary["inference_boundary"]) == ("transferable", "partial", "unsupported")
    for label in ("transferable", "partial", "unsupported"):
        assert boundary in result["explanations"][label]
    assert result["explanations"]["direct"]
    assert boundary["boundary_target"]["text"] == "数据库锁定所有权"
    assert "不适合" not in boundary["explanation"]


def test_ownership_and_jd_specific_claims_are_not_default_gaps(query_env):
    result = query(query_env, evidence_profile(query_env[2], []))
    for key in ("cdm-lock-gap", "cdm-edc-build-requirement"):
        result_item = item(result, key)
        assert result_item["inference_boundary"] == "jd_dependent"
        assert result_item["assessment_status"] == "not_assessable_without_jd"
        assert result_item["display_labels"] == []
    # A core support claim with no evidence is assessed separately.
    assert item(result)["display_labels"] == ["gap"]


def test_explicit_jd_applicability_yields_only_the_specific_gap(query_env):
    profile = evidence_profile(query_env[2], ["edc_build_evidence"])
    context = context_for(query_env)
    result = query(query_env, profile, jd_context=context)
    assert item(result, "cdm-lock-gap")["display_labels"] == ["gap"]
    assert item(result, "cdm-lock-gap")["missing_capability_codes"] == ["database_lock_evidence"]
    edc = item(result, "cdm-edc-build-requirement")
    assert edc["assessment_status"] == "not_applicable_to_jd"
    assert not edc["display_labels"]


def test_senior_requirement_requires_explicit_senior_jd(query_env):
    root, db, profile = query_env
    path = root / "data/career-map/career-card-match-rules-v1.json"
    data = read_json(path)
    next(rule for rule in data["rules"] if rule["rule_key"] == "cdm-edc-build-requirement")["applicability"] = "senior_only"
    write_json(path, data); build(root, db)
    assert item(query(query_env), "cdm-edc-build-requirement")["display_labels"] == []
    context = context_for(query_env, "cdm-edc-build-requirement", seniority="entry")
    entry = item(query(query_env, jd_context=context), "cdm-edc-build-requirement")
    assert entry["assessment_status"] == "not_assessable_without_senior_jd"
    assert not entry["display_labels"]
    context["seniority"] = "senior"
    assert item(query(query_env, jd_context=context), "cdm-edc-build-requirement")["display_labels"] == ["gap"]


@pytest.mark.parametrize("change,message", [
    ("unknown_code", "unknown capability code"),
    ("duplicate_id", "duplicate evidence_id"),
    ("bad_scope", "scope"),
    ("unconfirmed", "evidence_status"),
    ("missing_statement", "profile"),
    ("real_profile", "profile_type"),
])
def test_service_rejects_invalid_profile(query_env, change, message):
    profile = copy.deepcopy(query_env[2])
    if change == "unknown_code": profile["evidence"][0]["capability_codes"].append("not_registered")
    if change == "duplicate_id": profile["evidence"][1]["evidence_id"] = profile["evidence"][0]["evidence_id"]
    if change == "bad_scope": profile["evidence"][0]["scope"] = "superhero"
    if change == "unconfirmed": profile["evidence"][0]["evidence_status"] = "inferred"
    if change == "missing_statement": profile["evidence"][0].pop("statement")
    if change == "real_profile": profile["profile_type"] = "user_confirmed"
    with pytest.raises(ValueError, match=message): query(query_env, profile)


def test_valid_but_disallowed_scope_does_not_support_direct_claim(query_env):
    profile = evidence_profile(query_env[2], ["crf_checking", "data_query_follow_up", "gcp_training"], "academic_exercise")
    result = item(query(query_env, profile))
    assert result["evidence_relation"] == "none" and result["support_completeness"] == "no_evidence"
    assert result["profile_evidence_ids"] == []


def test_background_research_is_not_claim_support_and_provenance_is_complete(query_env):
    result = query(query_env)
    required = {"profile_evidence_ids", "career_card_claim_id", "career_card_revision", "role_pack_revision",
                "role_pack_boundary_id", "match_rule_revision", "knowledge_snapshot_id", "jd_evidence_snapshot_ids",
                "jd_evidence_status", "input_digest"}
    for value in result["items"]:
        assert required.issubset(value["provenance"])
        assert value["provenance"]["career_card_claim_id"]
        assert value["provenance"]["knowledge_snapshot_id"] == result["knowledge_snapshot_id"]
        assert value["provenance"]["input_digest"] == result["input_digest"]
        assert value["source_evidence_state"] == "background_research_only"
        assert value["claim_support_snapshot_ids"] == []
        assert all(source["relations"] == ["research_background"] for source in value["provenance"]["jd_evidence"])
    assert rows(query_env[1], "SELECT COUNT(*) FROM career_card_claim_snapshot_evidence WHERE relation_kind = 'claim_support'") == [(0,)]


def test_only_explicit_reviewed_annotation_creates_claim_support(query_env):
    root, db, _ = query_env
    path = root / f"data/career_cards/{CDM}.v1.json"
    card = read_json(path)
    card["jd_evidence"]["claim_support"] = [{
        "claim": {"kind": "transferable_direct", "text": card["transferability"]["direct"][0]},
        "snapshot_ids": ["cdm-01"], "reviewed_by": "synthetic-test-reviewer",
        "reviewed_at": "2026-09-05", "review_note": "Synthetic explicit support annotation for test only.",
    }]
    write_json(path, card); build(root, db)
    direct = item(query(query_env))
    assert direct["source_evidence_state"] == "reviewed_claim_support"
    assert len(direct["claim_support_snapshot_ids"]) == 1
    assert rows(db, "SELECT COUNT(*) FROM career_card_claim_snapshot_evidence WHERE relation_kind = 'claim_support'") == [(1,)]
    transfer = item(query(query_env), "cdm-quantitative-transferable")
    assert transfer["claim_support_snapshot_ids"] == []


def test_unreviewed_support_annotation_is_rejected(query_env):
    root, db, _ = query_env
    path = root / f"data/career_cards/{CDM}.v1.json"
    card = read_json(path)
    card["jd_evidence"]["claim_support"] = [{"claim": {"kind": "transferable_direct", "text": card["transferability"]["direct"][0]}, "snapshot_ids": ["cdm-01"]}]
    write_json(path, card)
    with pytest.raises(ValueError, match="career card"): build(root, db)


def test_deprecated_source_is_visible_and_cannot_establish_jd_applicability(query_env):
    root, db, _ = query_env
    before = query(query_env)
    card = read_json(root / f"data/career_cards/{CDM}.v1.json")
    path = root / card["jd_evidence"]["source_file"]
    data = read_json(path)
    next(ref for ref in data["jd_snapshots"] if ref["id"] == "cdm-01")["source_status"] = "deprecated"
    write_json(path, data); build(root, db)
    now = query(query_env)
    statuses = item(now)["provenance"]["jd_evidence_status"]
    assert any(status["source_status"] == "deprecated" and not status["usable"] for status in statuses)
    conditional = item(query(query_env, jd_context=context_for(query_env)), "cdm-lock-gap")
    assert conditional["assessment_status"] == "not_assessable_with_deprecated_jd"
    assert "gap" not in conditional["display_labels"]
    assert query(query_env, knowledge_snapshot_id=before["knowledge_snapshot_id"]) == before


def test_historical_replay_ignores_later_rule_revocation_and_current_card(query_env):
    root, db, _ = query_env
    before = query(query_env)
    rule_path = root / "data/career-map/career-card-match-rules-v1.json"
    rules = read_json(rule_path); rules["rules"] = [rule for rule in rules["rules"] if rule["rule_key"] != RULE]; write_json(rule_path, rules)
    card_path = root / f"data/career_cards/{CDM}.v1.json"
    card = read_json(card_path); card["summary"] += " Synthetic revision."; write_json(card_path, card)
    build(root, db)
    current = query(query_env)
    assert current["knowledge_snapshot_id"] != before["knowledge_snapshot_id"]
    assert not current["explanations"]["direct"]
    assert query(query_env, knowledge_snapshot_id=before["knowledge_snapshot_id"]) == before
    assert query(query_env, knowledge_snapshot_id=current["knowledge_snapshot_id"]) == current


def test_input_digest_is_stable_but_changes_with_input_or_jd_context(query_env):
    first = query(query_env)
    assert query(query_env) == first
    altered = copy.deepcopy(query_env[2]); altered["evidence"][0]["statement"] += " Additional synthetic note."
    assert query(query_env, altered)["input_digest"] != first["input_digest"]
    assert query(query_env, jd_context=context_for(query_env))["input_digest"] != first["input_digest"]


@pytest.mark.parametrize("change,message", [("claim_kind", "classification / claim kind"), ("transfer_to_direct", "transferable claim"), ("unknown_code", "unknown rule capability"), ("core_ownership", "default role gap")])
def test_invalid_rule_contract_is_rejected_on_import(query_env, change, message):
    root, db, _ = query_env
    path = root / "data/career-map/career-card-match-rules-v1.json"
    data = read_json(path)
    if change == "claim_kind": data["rules"][0]["claim"]["kind"] = "transferable"
    if change == "transfer_to_direct": next(rule for rule in data["rules"] if rule["classification"] == "transferable")["evidence_relation"] = "direct"
    if change == "unknown_code": data["rules"][0]["required_capability_codes"] = ["unknown_capability"]
    if change == "core_ownership": next(rule for rule in data["rules"] if rule["rule_key"] == "cdm-lock-gap")["applicability"] = "role_core"
    write_json(path, data)
    with pytest.raises(ValueError, match=message): build(root, db)


def test_wrong_target_and_unknown_jd_context_are_rejected(query_env):
    with pytest.raises(LookupError, match="Career Card"):
        CareerCardExplanationService(query_env[1]).explain(profile=query_env[2], role_pack="does_not_exist_v1")
    context = context_for(query_env); context["jd_evidence_snapshot_ids"] = ["unrelated-snapshot"]
    with pytest.raises(ValueError, match="outside"): query(query_env, jd_context=context)


def test_incompatible_pr1_snapshot_is_not_silently_reinterpreted(query_env):
    db = query_env[1]
    legacy = copy.deepcopy(manifest(db)); legacy["schema_version"] = "career-map-knowledge-snapshot-v1"; legacy["explanation_interpreter"]["version"] = "career-card-explanation-v1"
    with sqlite3.connect(db) as connection:
        connection.execute("INSERT INTO knowledge_snapshots VALUES (?, ?, ?, ?, ?, 0, ?)",
                           ("old-interpreter", digest(legacy), json.dumps(legacy), "career-card-explanation-v1", "career-map-import-v3", "2026-09-05"))
    with pytest.raises(ValueError, match="incompatible historical snapshot interpreter"):
        query(query_env, knowledge_snapshot_id="old-interpreter")


def test_snapshot_pins_capability_registry_for_input_validation(query_env):
    root, db, original = query_env
    old = query(query_env)
    path = root / "data/career-map/capabilities-v1.json"
    registry = read_json(path); registry["capability_codes"].append("new_synthetic_capability"); write_json(path, registry)
    build(root, db)
    profile = evidence_profile(original, ["new_synthetic_capability"])
    assert query(query_env, profile)["input_digest"]
    with pytest.raises(ValueError, match="unknown capability code"):
        query(query_env, profile, knowledge_snapshot_id=old["knowledge_snapshot_id"])


def test_legacy_all_card_links_migrate_only_to_background(query_env):
    root, db, _ = query_env
    with sqlite3.connect(db) as connection:
        connection.execute("""INSERT OR IGNORE INTO career_card_claim_jd_evidence
            SELECT e.career_card_claim_id, s.jd_evidence_id FROM career_card_claim_snapshot_evidence e
            JOIN jd_evidence_snapshots s ON s.jd_evidence_snapshot_id = e.jd_evidence_snapshot_id""")
        connection.execute("DROP TABLE career_card_claim_snapshot_evidence")
    build(root, db)
    assert rows(db, "SELECT COUNT(*) FROM career_card_claim_snapshot_evidence WHERE relation_kind = 'claim_support'") == [(0,)]
    assert all(value["source_evidence_state"] == "background_research_only" for value in query(query_env)["items"])


def test_deprecated_reviewed_source_does_not_count_as_usable_claim_support(query_env):
    root, db, _ = query_env
    card_path = root / f"data/career_cards/{CDM}.v1.json"
    card = read_json(card_path)
    card["jd_evidence"]["claim_support"] = [{
        "claim": {"kind": "transferable_direct", "text": card["transferability"]["direct"][0]},
        "snapshot_ids": ["cdm-01"], "reviewed_by": "synthetic-reviewer",
        "reviewed_at": "2026-09-05", "review_note": "Synthetic review record.",
    }]
    write_json(card_path, card); build(root, db)
    before = query(query_env)
    assert item(before)["claim_support_snapshot_ids"]
    path = root / card["jd_evidence"]["source_file"]
    data = read_json(path)
    next(ref for ref in data["jd_snapshots"] if ref["id"] == "cdm-01")["status"] = "deprecated"
    write_json(path, data); build(root, db)
    now = item(query(query_env))
    assert now["claim_support_snapshot_ids"] == []
    assert any("claim_support" in ref["relations"] and not ref["evidence_status"]["usable"] for ref in now["provenance"]["jd_evidence"])
    assert query(query_env, knowledge_snapshot_id=before["knowledge_snapshot_id"]) == before



def test_unsupported_label_cannot_upgrade_a_transferable_claim_to_direct(query_env):
    root, db, _ = query_env
    path = root / "data/career-map/career-card-match-rules-v1.json"
    data = read_json(path)
    rule = next(rule for rule in data["rules"] if rule["rule_key"] == "cdm-data-cleaning-boundary")
    rule["evidence_relation"] = "direct"
    write_json(path, data)
    with pytest.raises(ValueError, match="transferable claim"):
        build(root, db)


def test_draft_source_is_not_usable_for_jd_applicability(query_env):
    root, db, _ = query_env
    card = read_json(root / f"data/career_cards/{CDM}.v1.json")
    path = root / card["jd_evidence"]["source_file"]
    data = read_json(path)
    next(ref for ref in data["jd_snapshots"] if ref["id"] == "cdm-01")["source_status"] = "draft"
    write_json(path, data); build(root, db)
    result = query(query_env, jd_context=context_for(query_env))
    assert "gap" not in item(result, "cdm-lock-gap")["display_labels"]
    assert any(status["source_status"] == "draft" and not status["usable"] for status in item(result)["provenance"]["jd_evidence_status"])
