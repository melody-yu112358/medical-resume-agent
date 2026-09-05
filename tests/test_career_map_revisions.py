"""Lifecycle regressions against mutable temporary source trees, never canonical files."""
import json
import shutil
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import import_role_packs_to_career_map as importer
from career_map_revisions import content_digest
from medical_career_agent.services.career_card_explanation import CareerCardExplanationService

CDM = "clinical_data_management"
PACK = f"{CDM}_v1"
RULE = "cdm-assigned-data-quality-support"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


@pytest.fixture()
def source_tree(tmp_path, monkeypatch):
    root = tmp_path / "sources"
    for relative in ("data/role-packs", "data/career_cards", "data/career-map"):
        shutil.copytree(ROOT / relative, root / relative)
    for path in (root / "data/career_cards").glob("*.json"):
        relative = read_json(path)["jd_evidence"]["source_file"]
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    monkeypatch.setattr(importer, "ROOT", root)
    return root


def build(root, db):
    return importer.import_packs(
        db, root / "data/role-packs", root / "data/career-map/directions-v1.json",
        root / "data/career_cards", root / "data/career-map/career-card-match-rules-v1.json",
    )


def rows(db, sql, params=()):
    with sqlite3.connect(db) as connection:
        return connection.execute(sql, params).fetchall()


def manifest(db):
    return json.loads(rows(db, "SELECT manifest_json FROM knowledge_snapshots WHERE is_current = 1")[0][0])


def explain(db):
    profile = read_json(ROOT / "data/career-map/career-card-explanation-test-profiles-v1.json")["profiles"][0]
    return CareerCardExplanationService(db).explain(profile=profile, role_pack=PACK)


def current_ids(db):
    return (
        rows(db, "SELECT role_pack_version_id FROM role_pack_versions WHERE external_key = ? AND is_current = 1", (PACK,))[0][0],
        rows(db, "SELECT career_card_version_id FROM career_cards WHERE career_card_id = ? AND is_current = 1", (CDM,))[0][0],
        rows(db, "SELECT career_card_match_rule_id FROM career_card_match_rules WHERE rule_key = ? AND lifecycle_status = 'current'", (RULE,))[0][0],
    )


def effective_state(db):
    """Compare all active projections without machine-local metadata or history."""
    result = {"manifest": manifest(db), "explanation": explain(db)}
    for table in ("ecosystems", "lifecycle_stages", "function_families"):
        result[table] = rows(db, f"SELECT code, label FROM {table} ORDER BY code")
    for table in ("role_ecosystems", "role_lifecycle_stages", "role_function_families",
                  "career_direction_ecosystems", "career_direction_lifecycle_stages", "career_direction_function_families",
                  "role_jd_evidence"):
        result[table] = sorted(rows(db, f"SELECT * FROM {table}"))
    result["directions"] = rows(db, """SELECT external_key, label, knowledge_maturity, service_mode,
        runtime_status, requires_specific_jd, summary, boundary_note, source_sha256
        FROM career_directions WHERE deprecated_at IS NULL ORDER BY external_key""")
    for table in ("role_skills", "role_requirements", "negative_mappings", "role_expression_policies", "role_pack_evaluation_cases"):
        result[table] = sorted(rows(db, f"SELECT r.* FROM {table} r JOIN role_pack_versions v ON v.role_pack_version_id = r.role_pack_version_id WHERE v.is_current = 1"))
    result["claims"] = sorted(rows(db, "SELECT c.* FROM career_card_claims c JOIN career_cards v ON c.career_card_version_id = v.career_card_version_id WHERE v.is_current = 1"))
    result["claim_jd"] = sorted(rows(db, """SELECT j.* FROM career_card_claim_jd_evidence j
        JOIN career_card_claims c ON c.career_card_claim_id = j.career_card_claim_id
        JOIN career_cards v ON v.career_card_version_id = c.career_card_version_id WHERE v.is_current = 1"""))
    return result


def test_fresh_repeated_import_has_one_manifest_and_no_duplicate_events(source_tree, tmp_path):
    db = tmp_path / "map.sqlite"
    first = build(source_tree, db)
    state = effective_state(db)
    counts = {table: rows(db, f"SELECT COUNT(*) FROM {table}")[0][0] for table in (
        "source_artifacts", "knowledge_snapshots", "knowledge_snapshot_activations", "career_card_match_rule_events",
        "role_pack_versions", "career_cards", "career_card_match_rules", "jd_evidence_snapshots")}
    second = build(source_tree, db)
    assert first["new_versions"] == 10 and second["new_versions"] == 0
    assert first["knowledge_snapshot_id"] == second["knowledge_snapshot_id"]
    assert effective_state(db) == state
    for table, count in counts.items():
        assert rows(db, f"SELECT COUNT(*) FROM {table}")[0][0] == count
    snapshot = manifest(db)
    assert len(snapshot["role_pack_revisions"]) == 10
    assert len(snapshot["career_card_revisions"]) == 5
    assert len(snapshot["match_rule_revisions"]) == 11
    assert len(snapshot["jd_snapshot_revisions"]) == 44
    assert snapshot["taxonomy_revision"] and snapshot["explanation_interpreter"]["version"]
    assert first["source_digest"] == content_digest(snapshot)
    assert rows(db, "PRAGMA foreign_key_check") == []


@pytest.mark.parametrize("kind", ["pack", "card"])
def test_pack_and_card_updates_keep_history_and_explicit_binding(source_tree, tmp_path, kind):
    db = tmp_path / "map.sqlite"
    build(source_tree, db)
    old_pack, old_card, old_rule = current_ids(db)
    old_manifest = manifest(db)
    path = source_tree / (f"data/role-packs/{PACK}.json" if kind == "pack" else f"data/career_cards/{CDM}.v1.json")
    data = read_json(path)
    data["label" if kind == "pack" else "summary"] += " synthetic revision"
    write_json(path, data)
    build(source_tree, db)
    new_pack, new_card, new_rule = current_ids(db)
    assert (new_pack != old_pack) == (kind == "pack")
    assert new_card != old_card and new_rule != old_rule
    assert rows(db, "SELECT role_pack_version_id FROM career_cards WHERE career_card_version_id = ?", (new_card,)) == [(new_pack,)]
    assert rows(db, "SELECT is_current, superseded_by_version_id FROM career_cards WHERE career_card_version_id = ?", (old_card,)) == [(0, new_card)]
    assert rows(db, "SELECT lifecycle_status, superseded_by_rule_id FROM career_card_match_rules WHERE career_card_match_rule_id = ?", (old_rule,)) == [("superseded", new_rule)]
    assert old_manifest in [json.loads(row[0]) for row in rows(db, "SELECT manifest_json FROM knowledge_snapshots")]
    assert rows(db, "PRAGMA foreign_key_check") == []


def test_rule_revision_is_independent_immutable_and_reactivated(source_tree, tmp_path):
    db = tmp_path / "map.sqlite"
    build(source_tree, db)
    old_ids = current_ids(db)
    original_manifest = manifest(db)
    path = source_tree / "data/career-map/career-card-match-rules-v1.json"
    original_bytes = path.read_bytes()
    data = read_json(path)
    data["rules"][0]["explanation"] = "Synthetic revised explanation"
    write_json(path, data)
    build(source_tree, db)
    new_ids = current_ids(db)
    assert old_ids[:2] == new_ids[:2] and old_ids[2] != new_ids[2]
    assert explain(db)["explanations"]["direct"][0]["explanation"] == "Synthetic revised explanation"
    assert rows(db, "SELECT COUNT(*) FROM career_card_match_rules")[0][0] == 12
    with sqlite3.connect(db) as connection, pytest.raises(sqlite3.IntegrityError, match="immutable"):
        connection.execute("UPDATE career_card_match_rules SET explanation = 'mutated' WHERE career_card_match_rule_id = ?", (old_ids[2],))
    path.write_bytes(original_bytes)
    build(source_tree, db)
    assert current_ids(db) == old_ids
    assert manifest(db) == original_manifest
    assert rows(db, "SELECT COUNT(*) FROM knowledge_snapshot_activations")[0][0] == 3
    events = rows(db, "SELECT lifecycle_status FROM career_card_match_rule_events WHERE career_card_match_rule_id = ?", (old_ids[2],))
    assert sorted(row[0] for row in events) == ["current", "current", "superseded"]


@pytest.mark.parametrize("remove_all", [False, True])
def test_rule_removal_revokes_and_readdition_records_history(source_tree, tmp_path, remove_all):
    db = tmp_path / "map.sqlite"
    build(source_tree, db)
    old_rule = current_ids(db)[2]
    path = source_tree / "data/career-map/career-card-match-rules-v1.json"
    original = path.read_bytes()
    data = read_json(path)
    data["rules"] = [] if remove_all else data["rules"][1:]
    write_json(path, data)
    build(source_tree, db)
    assert rows(db, "SELECT lifecycle_status FROM career_card_match_rules WHERE career_card_match_rule_id = ?", (old_rule,)) == [("revoked",)]
    assert rows(db, "SELECT COUNT(*) FROM career_card_match_rules WHERE lifecycle_status = 'current'")[0][0] == (0 if remove_all else 10)
    if remove_all:
        with pytest.raises(LookupError, match="no explanation match rules"):
            explain(db)
    else:
        assert explain(db)["explanations"]["direct"] == []
    path.write_bytes(original)
    build(source_tree, db)
    assert current_ids(db)[2] == old_rule
    assert rows(db, "SELECT COUNT(*) FROM career_card_match_rules")[0][0] == 11
    assert sorted(row[0] for row in rows(db, "SELECT lifecycle_status FROM career_card_match_rule_events WHERE career_card_match_rule_id = ?", (old_rule,))) == ["current", "current", "revoked"]


def edit_taxonomy(root):
    path = root / "data/career-map/directions-v1.json"
    data = read_json(path)
    data["canonical_role_pack_taxonomy"][0]["ecosystems"] = []
    removed = data["jd_driven_directions"].pop()
    write_json(path, data)
    return data["canonical_role_pack_taxonomy"][0]["role_pack"], removed["external_key"]


def test_taxonomy_removal_replaces_current_links_but_retains_registry(source_tree, tmp_path):
    db = tmp_path / "map.sqlite"
    build(source_tree, db)
    old_manifest = manifest(db)
    key, removed = edit_taxonomy(source_tree)
    build(source_tree, db)
    assert rows(db, """SELECT r.* FROM role_ecosystems r JOIN role_pack_versions p
        ON p.role_pack_version_id = r.role_pack_version_id WHERE p.external_key = ? AND p.is_current = 1""", (key,)) == []
    assert rows(db, "SELECT external_key FROM career_map_entries WHERE external_key = ?", (removed,)) == []
    assert rows(db, "SELECT runtime_status FROM career_directions WHERE external_key = ?", (removed,)) == [("deprecated",)]
    assert rows(db, "SELECT raw_content FROM source_artifacts WHERE artifact_id = ?", (old_manifest["taxonomy_revision"],))
    assert manifest(db)["taxonomy_revision"] != old_manifest["taxonomy_revision"]


@pytest.mark.parametrize("metadata_only", [False, True])
def test_jd_revision_does_not_accumulate_or_mutate_old_card_evidence(source_tree, tmp_path, metadata_only):
    db = tmp_path / "map.sqlite"
    build(source_tree, db)
    old_card = current_ids(db)[1]
    old_manifest = manifest(db)
    card = read_json(source_tree / f"data/career_cards/{CDM}.v1.json")
    path = source_tree / card["jd_evidence"]["source_file"]
    data = read_json(path)
    snapshot = next(item for item in data["jd_snapshots"] if item["id"] == "cdm-01")
    snapshot["retrieved_at"] = "2026-09-05" if metadata_only else snapshot["retrieved_at"]
    if not metadata_only:
        snapshot["source_snapshot"] += " Synthetic JD revision."
    write_json(path, data)
    build(source_tree, db)
    assert current_ids(db)[1] != old_card
    assert len(explain(db)["explanations"]["direct"][0]["provenance"]["jd_evidence"]) == 8
    assert rows(db, "SELECT COUNT(*) FROM career_card_jd_snapshots WHERE career_card_version_id = ?", (old_card,)) == [(8,)]
    assert old_manifest in [json.loads(row[0]) for row in rows(db, "SELECT manifest_json FROM knowledge_snapshots")]
    fresh = tmp_path / "fresh.sqlite"
    build(source_tree, fresh)
    assert effective_state(db) == effective_state(fresh)


def test_import_failure_rolls_back_all_data_and_activation(source_tree, tmp_path):
    db = tmp_path / "map.sqlite"
    build(source_tree, db)
    with sqlite3.connect(db) as connection:
        before = list(connection.iterdump())
    edit_taxonomy(source_tree)
    path = source_tree / "data/career-map/career-card-match-rules-v1.json"
    data = read_json(path)
    data["rules"][-1]["negative_mapping_text"] = "missing boundary reference"
    write_json(path, data)
    with pytest.raises(ValueError, match="no Role Pack negative mapping"):
        build(source_tree, db)
    with sqlite3.connect(db) as connection:
        assert list(connection.iterdump()) == before


def test_fresh_and_incremental_match_after_combined_updates(source_tree, tmp_path):
    db = tmp_path / "incremental.sqlite"
    build(source_tree, db)
    path = source_tree / f"data/role-packs/{PACK}.json"
    data = read_json(path); data["label"] += " synthetic change"; write_json(path, data)
    path = source_tree / f"data/career_cards/{CDM}.v1.json"
    data = read_json(path); data["summary"] += " synthetic change"; write_json(path, data)
    path = source_tree / "data/career-map/career-card-match-rules-v1.json"
    data = read_json(path); data["rules"][0]["explanation"] += " synthetic change"; data["rules"].pop(); write_json(path, data)
    edit_taxonomy(source_tree)
    build(source_tree, db)
    fresh = tmp_path / "fresh.sqlite"
    build(source_tree, fresh)
    assert effective_state(db) == effective_state(fresh)


def test_unique_current_revision_constraints_and_immutable_manifest(source_tree, tmp_path):
    db = tmp_path / "map.sqlite"
    build(source_tree, db)
    path = source_tree / f"data/role-packs/{PACK}.json"
    data = read_json(path); data["label"] += " synthetic change"; write_json(path, data)
    build(source_tree, db)
    for table in ("role_pack_versions", "career_cards", "knowledge_snapshots"):
        with sqlite3.connect(db) as connection, pytest.raises(sqlite3.IntegrityError, match="UNIQUE"):
            connection.execute(f"UPDATE {table} SET is_current = 1 WHERE is_current = 0")
    with sqlite3.connect(db) as connection, pytest.raises(sqlite3.IntegrityError, match="UNIQUE"):
        connection.execute("UPDATE career_card_match_rules SET lifecycle_status = 'current' WHERE lifecycle_status = 'superseded'")
    with sqlite3.connect(db) as connection, pytest.raises(sqlite3.IntegrityError, match="immutable"):
        connection.execute("UPDATE knowledge_snapshots SET manifest_json = '{}'")


def make_legacy_database(root, db, staging):
    """Project baseline data into the frozen pre-PR DDL with its original IDs."""
    build(root, staging)
    with sqlite3.connect(staging) as source, sqlite3.connect(db) as target:
        target.executescript((ROOT / "tests/fixtures/career_map_v2.sql").read_text(encoding="utf-8"))
        id_map = {}
        for revision, key, digest in source.execute("SELECT career_card_version_id, career_card_id, content_sha256 FROM career_cards"):
            id_map[revision] = importer.stable_id("career-card-version", key, digest)
        for revision, card, kind, text in source.execute("SELECT career_card_claim_id, career_card_version_id, claim_kind, claim_text FROM career_card_claims"):
            id_map[revision] = importer.stable_id("career-card-claim", id_map[card], kind, text)
        for revision, card, key in source.execute("SELECT career_card_match_rule_id, career_card_version_id, rule_key FROM career_card_match_rules"):
            id_map[revision] = importer.stable_id("career-card-match-rule", id_map[card], key)
        for revision, evidence, external, digest in source.execute("SELECT jd_evidence_snapshot_id, jd_evidence_id, external_snapshot_id, source_digest_sha256 FROM jd_evidence_snapshots"):
            id_map[revision] = importer.stable_id("jd-evidence-snapshot", evidence, external, digest)
        tables = [row[0] for row in target.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        for table in tables:
            columns = [row[1] for row in target.execute(f"PRAGMA table_info({table})")]
            values = [[id_map.get(value, value) for value in row] for row in source.execute(f"SELECT {', '.join(columns)} FROM {table}")]
            target.executemany(f"INSERT INTO {table} VALUES ({', '.join('?' for _ in columns)})", values)
    return id_map


def test_legacy_schema_upgrade_preserves_ids_and_matches_fresh(source_tree, tmp_path):
    db = tmp_path / "legacy.sqlite"
    id_map = make_legacy_database(source_tree, db, tmp_path / "staging.sqlite")
    build(source_tree, db)
    fresh = tmp_path / "fresh.sqlite"
    build(source_tree, fresh)
    assert effective_state(db) == effective_state(fresh)
    for table, column in (("career_cards", "career_card_version_id"), ("career_card_match_rules", "career_card_match_rule_id"), ("jd_evidence_snapshots", "jd_evidence_snapshot_id")):
        retained = {row[0] for row in rows(db, f"SELECT {column} FROM {table}")}
        assert retained.intersection(id_map.values())
    assert rows(db, "PRAGMA foreign_key_check") == []
    build(source_tree, db)
    assert effective_state(db) == effective_state(fresh)


def test_failed_legacy_upgrade_rolls_back_schema_and_rows(source_tree, tmp_path):
    db = tmp_path / "legacy.sqlite"
    make_legacy_database(source_tree, db, tmp_path / "staging.sqlite")
    with sqlite3.connect(db) as connection:
        before = list(connection.iterdump())
    path = source_tree / "data/career-map/career-card-match-rules-v1.json"
    data = read_json(path); data["rules"][-1]["negative_mapping_text"] = "missing boundary"; write_json(path, data)
    with pytest.raises(ValueError, match="no Role Pack negative mapping"):
        build(source_tree, db)
    with sqlite3.connect(db) as connection:
        assert list(connection.iterdump()) == before
        assert "revision_sha256" not in {row[1] for row in connection.execute("PRAGMA table_info(career_cards)")}
