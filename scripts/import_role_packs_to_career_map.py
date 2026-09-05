#!/usr/bin/env python3
"""Import canonical Role Pack JSON into the local career-map SQL projection.

The JSON files remain the editable source of truth. This script validates those
files, records their raw content and SHA-256 digest, then builds an idempotent
SQLite projection using the PostgreSQL-compatible DDL in database/.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from career_map_revisions import (
    activate_rules, activate_versions, apply_schema, canonical_json, content_digest,
    needs_legacy_upgrade, save_snapshot,
)


ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = ROOT / "data" / "role-packs"
SCHEMA_PATH = ROOT / "schemas" / "role-pack.schema.json"
DDL_PATH = ROOT / "database" / "career_map_schema.sql"
CAREER_MAP_DIRECTIONS_PATH = ROOT / "data" / "career-map" / "directions-v1.json"
CAREER_CARD_DIR = ROOT / "data" / "career_cards"
CAREER_CARD_SCHEMA_PATH = ROOT / "schemas" / "career-card.schema.json"
CAREER_CARD_MATCH_RULES_PATH = ROOT / "data" / "career-map" / "career-card-match-rules-v1.json"
CAREER_CARD_MATCH_RULES_SCHEMA_PATH = ROOT / "schemas" / "career-card-match-rules.schema.json"
IMPORTER_VERSION = "career-map-import-v3"
INTERPRETER_PATH = ROOT / "src" / "medical_career_agent" / "services" / "career_card_explanation.py"
sys.path.insert(0, str(ROOT / "src"))
from medical_career_agent.services.career_card_explanation import QUERY_VERSION  # noqa: E402
UUID_NAMESPACE = uuid.UUID("b2c09a52-74c0-4e80-9ea5-bf5f4a54ec56")
ROLE_PACK_PATTERN = re.compile(r"^(?P<name>[a-z_][a-z0-9_]*)_(?P<version>v[0-9]+)$")


def stable_id(*parts: str) -> str:
    return str(uuid.uuid5(UUID_NAMESPACE, "\0".join(parts)))


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_packs(pack_dir: Path = PACK_DIR) -> list[tuple[Path, bytes, dict[str, Any]]]:
    packs: list[tuple[Path, bytes, dict[str, Any]]] = []
    for path in sorted(pack_dir.glob("*.json")):
        raw = path.read_bytes()
        packs.append((path, raw, json.loads(raw.decode("utf-8"))))
    if not packs:
        raise ValueError(f"No Role Pack JSON files found in {pack_dir}")
    return packs


def validate_pack(pack: dict[str, Any], schema: dict[str, Any]) -> None:
    """Use the repository JSON Schema when available, plus a stable ID check."""
    try:
        from jsonschema import validate
    except ImportError as error:  # pragma: no cover - documented runtime guard
        raise RuntimeError(
            "Schema validation requires jsonschema. Install the schema_validation extra."
        ) from error

    validate(instance=pack, schema=schema)
    if not ROLE_PACK_PATTERN.fullmatch(pack["role_pack"]):
        raise ValueError(f"Invalid Role Pack identifier: {pack['role_pack']}")


def validate_career_card(card: dict[str, Any], schema: dict[str, Any]) -> None:
    try:
        from jsonschema import validate
    except ImportError as error:  # pragma: no cover - documented runtime guard
        raise RuntimeError(
            "Schema validation requires jsonschema. Install the schema_validation extra."
        ) from error
    validate(instance=card, schema=schema)


def load_career_cards(career_card_dir: Path = CAREER_CARD_DIR) -> list[tuple[Path, bytes, dict[str, Any]]]:
    cards: list[tuple[Path, bytes, dict[str, Any]]] = []
    for path in sorted(career_card_dir.glob("*.json")):
        raw = path.read_bytes()
        cards.append((path, raw, json.loads(raw.decode("utf-8"))))
    return cards


def load_career_card_match_rules(
    path: Path = CAREER_CARD_MATCH_RULES_PATH,
) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    return raw, json.loads(raw.decode("utf-8"))


def load_direction_registry(path: Path = CAREER_MAP_DIRECTIONS_PATH) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    registry = json.loads(raw.decode("utf-8"))
    required = {"schema_version", "taxonomy", "canonical_role_pack_taxonomy", "jd_driven_directions", "beta_directions"}
    missing = required - registry.keys()
    if missing or registry["schema_version"] != "career-map-directions-v1":
        raise ValueError(f"Invalid career-map directions registry; missing={sorted(missing)}")
    for dimension in ("ecosystems", "lifecycle_stages", "function_families"):
        entries = registry["taxonomy"].get(dimension, [])
        if not entries or any(not item.get("code") or not item.get("label") for item in entries):
            raise ValueError(f"Invalid taxonomy dimension: {dimension}")
    return raw, registry


def insert_or_ignore(connection: sqlite3.Connection, statement: str, values: tuple[Any, ...]) -> None:
    connection.execute(statement, values)


def import_packs(
    database_path: Path,
    pack_dir: Path = PACK_DIR,
    directions_path: Path = CAREER_MAP_DIRECTIONS_PATH,
    career_card_dir: Path = CAREER_CARD_DIR,
    career_card_match_rules_path: Path = CAREER_CARD_MATCH_RULES_PATH,
) -> dict[str, int | str]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    career_card_schema = json.loads(CAREER_CARD_SCHEMA_PATH.read_text(encoding="utf-8"))
    career_card_match_rules_schema = json.loads(
        CAREER_CARD_MATCH_RULES_SCHEMA_PATH.read_text(encoding="utf-8")
    )
    packs = load_packs(pack_dir)
    for _, _, pack in packs:
        validate_pack(pack, schema)
    directions_raw, directions = load_direction_registry(directions_path)
    career_cards = load_career_cards(career_card_dir)
    for _, _, card in career_cards:
        validate_career_card(card, career_card_schema)
    match_rules_raw, match_rules = load_career_card_match_rules(career_card_match_rules_path)
    validate_career_card(match_rules, career_card_match_rules_schema)
    canonical_keys = {pack["role_pack"] for _, _, pack in packs}
    taxonomy_keys = {item["role_pack"] for item in directions["canonical_role_pack_taxonomy"]}
    if canonical_keys != taxonomy_keys:
        raise ValueError("Career-map taxonomy must classify exactly the current canonical Role Pack set")

    # Capture dependencies once; the manifest and projection use the same bytes.
    candidates = {}
    for _, _, card in career_cards:
        candidate_path = (ROOT / card["jd_evidence"]["source_file"]).resolve()
        if not candidate_path.is_relative_to(ROOT.resolve()):
            raise ValueError("Career card evidence path escapes repository")
        candidates[candidate_path] = candidate_path.read_bytes()
    sources = [(path, raw) for path, raw, _ in packs + career_cards]
    sources += [(directions_path, directions_raw), (career_card_match_rules_path, match_rules_raw)]
    sources += list(candidates.items())
    source_records = [{"path": path.relative_to(ROOT).as_posix(), "content_sha256": sha256(raw)}
                      for path, raw in sources]
    source_records = list({item["path"]: item for item in source_records}.values())
    for items, key in (([pack for _, _, pack in packs], "role_pack"),
                       ([card for _, _, card in career_cards], "career_card_id")):
        if len({item[key] for item in items}) != len(items):
            raise ValueError(f"Duplicate source identity: {key}")
    rule_keys = [(rule["career_card_id"], rule["rule_key"]) for rule in match_rules["rules"]]
    if len(set(rule_keys)) != len(rule_keys):
        raise ValueError("Duplicate match rule identity")

    database_path.parent.mkdir(parents=True, exist_ok=True)
    now = utc_now()
    schema_version = schema["x_schema_version"]
    with sqlite3.connect(database_path) as connection:
        upgrade = needs_legacy_upgrade(connection)
        # SQLite table-rebuild migrations require FK enforcement off before BEGIN.
        # All references are checked explicitly before the single commit below.
        connection.execute(f"PRAGMA foreign_keys = {'OFF' if upgrade else 'ON'}")
        connection.execute("BEGIN IMMEDIATE")
        upgrade = needs_legacy_upgrade(connection)
        apply_schema(connection, DDL_PATH.read_text(encoding="utf-8"), upgrade=upgrade)
        selected_packs = {}
        imported_versions = 0
        for path, raw, pack in packs:
            pack_key = pack["role_pack"]
            match = ROLE_PACK_PATTERN.fullmatch(pack_key)
            assert match is not None
            content_hash = sha256(raw)
            relative_path = path.relative_to(ROOT).as_posix()
            role_id = stable_id("role", pack_key)
            artifact_id = stable_id("artifact", relative_path, content_hash)
            version_id = stable_id("role-pack-version", pack_key, content_hash)

            connection.execute(
                """INSERT INTO roles (role_id, canonical_key, display_name, role_kind, created_at, updated_at)
                   VALUES (?, ?, ?, 'role_pack_family', ?, ?)
                   ON CONFLICT(canonical_key) DO UPDATE SET display_name = excluded.display_name,
                       updated_at = excluded.updated_at""",
                (role_id, pack_key, pack["label"], now, now),
            )
            insert_or_ignore(
                connection,
                """INSERT OR IGNORE INTO source_artifacts
                   (artifact_id, relative_path, content_sha256, raw_content, imported_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (artifact_id, relative_path, content_hash, raw.decode("utf-8"), now),
            )

            existing = connection.execute(
                "SELECT role_pack_version_id FROM role_pack_versions WHERE external_key = ? AND content_sha256 = ?",
                (pack_key, content_hash),
            ).fetchone()
            if existing is None:
                connection.execute(
                    """INSERT INTO role_pack_versions
                       (role_pack_version_id, role_id, external_key, version_label, label, target_scope,
                        boundary_note, schema_version, content_sha256, artifact_id, is_current, imported_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)""",
                    (
                        version_id,
                        role_id,
                        pack_key,
                        match.group("version"),
                        pack["label"],
                        pack["skill_reference"]["target_scope"],
                        pack["skill_reference"]["boundary_note"],
                        schema_version,
                        content_hash,
                        artifact_id,
                        now,
                    ),
                )
                imported_versions += 1
                _insert_projection_rows(connection, version_id, pack)
            else:
                version_id = existing[0]
            selected_packs[pack_key] = version_id

            insert_or_ignore(
                connection,
                """INSERT OR IGNORE INTO role_status_history
                   (role_status_history_id, role_pack_version_id, maturity_status, execution_status,
                    status_reason, provenance_path, recorded_at)
                   VALUES (?, ?, 'canonical_v1', 'canonical_source', ?, ?, ?)""",
                (
                    stable_id("status", version_id, "canonical_v1", "canonical_source"),
                    version_id,
                    "Canonical source is defined by data/role-packs/*.json; runtime routing is separate.",
                    relative_path,
                    now,
                ),
            )

        activate_versions(connection, "role_pack_versions", "role_pack_version_id", "external_key", selected_packs, now)
        _import_direction_registry(connection, directions_raw, directions, now, directions_path)
        # Role-to-JD is a current projection; exact historical links live on Card revisions.
        connection.execute("DELETE FROM role_jd_evidence")
        _import_career_cards(connection, career_cards, now, candidates)
        rule_changes = _import_career_card_match_rules(
            connection, match_rules_raw, match_rules, now, career_card_match_rules_path
        )
        snapshot_id, digest = save_snapshot(
            connection, sources=source_records,
            taxonomy_artifact_id=stable_id("artifact", directions_path.relative_to(ROOT).as_posix(), sha256(directions_raw)),
            rule_artifact_id=stable_id("artifact", career_card_match_rules_path.relative_to(ROOT).as_posix(), sha256(match_rules_raw)),
            interpreter={"version": QUERY_VERSION, "source_sha256": sha256(INTERPRETER_PATH.read_bytes().replace(b"\r\n", b"\n"))},
            importer_version=IMPORTER_VERSION, now=now, rule_changes=rule_changes,
        )
        connection.execute(
            """INSERT OR IGNORE INTO import_batches
               (import_id, source_root, source_digest_sha256, imported_at, importer_version)
               VALUES (?, ?, ?, ?, ?)""",
            (stable_id("import", str(pack_dir.resolve()), digest), str(pack_dir.resolve()), digest, now, IMPORTER_VERSION),
        )
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise sqlite3.IntegrityError(f"Career-map foreign key violations: {violations}")

    return {
        "role_packs": len(packs),
        "jd_driven_directions": len(directions["jd_driven_directions"]),
        "career_cards": len(career_cards),
        "career_card_match_rules": len(match_rules["rules"]),
        "new_versions": imported_versions,
        "source_digest": digest,
        "knowledge_snapshot_id": snapshot_id,
    }


def _import_career_cards(
    connection: sqlite3.Connection,
    career_cards: list[tuple[Path, bytes, dict[str, Any]]],
    now: str,
    candidates: dict[Path, bytes],
) -> None:
    selected_cards = {}
    for card_path, card_raw, card in career_cards:
        relative_card_path = card_path.relative_to(ROOT).as_posix()
        card_hash = sha256(card_raw)
        card_artifact_id = stable_id("artifact", relative_card_path, card_hash)
        insert_or_ignore(
            connection,
            """INSERT OR IGNORE INTO source_artifacts
               (artifact_id, relative_path, content_sha256, raw_content, imported_at)
               VALUES (?, ?, ?, ?, ?)""",
            (card_artifact_id, relative_card_path, card_hash, card_raw.decode("utf-8"), now),
        )
        role_row = connection.execute(
            "SELECT role_pack_version_id FROM role_pack_versions WHERE external_key = ? AND is_current = 1",
            (card["role_pack"],),
        ).fetchone()
        if role_row is None:
            raise ValueError(f"Career card {card['career_card_id']} references no current Role Pack: {card['role_pack']}")

        candidate_path = (ROOT / card["jd_evidence"]["source_file"]).resolve()
        if not candidate_path.is_relative_to(ROOT.resolve()):
            raise ValueError(f"Career card evidence path escapes repository: {card['jd_evidence']['source_file']}")
        if not candidate_path.is_file():
            raise ValueError(f"Career card evidence file does not exist: {card['jd_evidence']['source_file']}")
        candidate_raw = candidates[candidate_path]
        candidate = json.loads(candidate_raw.decode("utf-8"))
        if candidate.get("career_id") != card["career_card_id"]:
            raise ValueError(f"Career card {card['career_card_id']} does not match evidence career_id")
        snapshots = {snapshot["id"]: snapshot for snapshot in candidate.get("jd_snapshots", [])}
        selected_ids = card["jd_evidence"]["snapshot_ids"]
        unknown_ids = set(selected_ids) - snapshots.keys()
        if unknown_ids:
            raise ValueError(f"Career card {card['career_card_id']} references unknown JD snapshots: {sorted(unknown_ids)}")

        relative_candidate_path = candidate_path.relative_to(ROOT).as_posix()
        candidate_hash = sha256(candidate_raw)
        candidate_artifact_id = stable_id("artifact", relative_candidate_path, candidate_hash)
        insert_or_ignore(
            connection,
            """INSERT OR IGNORE INTO source_artifacts
               (artifact_id, relative_path, content_sha256, raw_content, imported_at)
               VALUES (?, ?, ?, ?, ?)""",
            (candidate_artifact_id, relative_candidate_path, candidate_hash, candidate_raw.decode("utf-8"), now),
        )

        evidence_ids, snapshot_ids = _import_jd_snapshots(
            connection,
            role_row[0],
            snapshots,
            selected_ids,
            candidate_artifact_id,
            now,
        )
        revision_hash = content_digest({"card_content": card_hash, "role_pack_revision": role_row[0],
                                        "jd_artifact": candidate_artifact_id})
        card_version_id = stable_id("career-card-version", card["career_card_id"], revision_hash)
        connection.execute(
            """INSERT OR IGNORE INTO career_cards
               (career_card_version_id, role_pack_version_id, career_card_id, version_label, summary,
                scope_note, content_sha256, artifact_id, is_current, imported_at, revision_sha256, jd_artifact_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)""",
            (card_version_id, role_row[0], card["career_card_id"], card["version"], card["summary"],
             card["scope_note"], card_hash, card_artifact_id, now, revision_hash, candidate_artifact_id),
        )
        selected_cards[card["career_card_id"]] = card_version_id
        _insert_career_card_claims(connection, card_version_id, card, evidence_ids)
        for snapshot_id in snapshot_ids:
            connection.execute("INSERT OR IGNORE INTO career_card_jd_snapshots VALUES (?, ?)", (card_version_id, snapshot_id))
    activate_versions(connection, "career_cards", "career_card_version_id", "career_card_id", selected_cards, now)



def _import_jd_snapshots(
    connection: sqlite3.Connection,
    role_pack_version_id: str,
    snapshots: dict[str, dict[str, Any]],
    selected_ids: list[str],
    source_artifact_id: str,
    now: str,
) -> tuple[list[str], list[str]]:
    evidence_ids: list[str] = []
    snapshot_ids: list[str] = []
    for snapshot_id in selected_ids:
        snapshot = snapshots[snapshot_id]
        source_snapshot = snapshot.get("source_snapshot")
        source_digest = snapshot.get("source_digest")
        required = ("employer", "title", "url", "retrieved_at", "status")
        missing = [key for key in required if not snapshot.get(key)]
        if missing or not source_snapshot or not source_digest:
            raise ValueError(f"JD snapshot {snapshot_id} is incomplete; missing={missing}")
        source_type = (
            snapshot.get("source_type")
            or snapshot.get("current_retrieval_status")
            or snapshot.get("retrieval_status")
            or "retained_candidate_evidence"
        )
        actual_digest = sha256(source_snapshot.encode("utf-8"))
        # Older frozen evidence may define source_digest over a broader retained
        # capture than the visible excerpt. Preserve both values rather than
        # silently replacing the declared provenance or discarding the record.
        evidence_id = stable_id("jd-evidence", snapshot["url"], actual_digest)
        evidence_ids.append(evidence_id)
        connection.execute(
            """INSERT INTO jd_evidence
               (jd_evidence_id, source_title, source_url, publisher, published_at, accessed_at, market,
                snapshot_sha256, source_status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, 'China', ?, 'reviewed', ?)
               ON CONFLICT(source_url, snapshot_sha256) DO UPDATE SET
                   source_title = excluded.source_title, publisher = excluded.publisher,
                   published_at = excluded.published_at, accessed_at = excluded.accessed_at""",
            (
                evidence_id,
                f"{snapshot['employer']} — {snapshot['title']}",
                snapshot["url"],
                snapshot["employer"],
                snapshot.get("published_at"),
                snapshot["retrieved_at"],
                actual_digest,
                now,
            ),
        )
        revision_hash = content_digest(snapshot)
        snapshot_row_id = stable_id("jd-evidence-snapshot", source_artifact_id, snapshot_id, revision_hash)
        snapshot_ids.append(snapshot_row_id)
        qualifying = snapshot.get("qualifying")
        connection.execute(
            """INSERT OR IGNORE INTO jd_evidence_snapshots
               (jd_evidence_snapshot_id, jd_evidence_id, external_snapshot_id, employer, job_title, location,
                retrieved_at, status, source_type, snapshot_completeness, qualifying, source_snapshot,
                source_digest_sha256, declared_source_digest_sha256, source_digest_matches, source_artifact_id, created_at, revision_sha256)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                snapshot_row_id,
                evidence_id,
                snapshot_id,
                snapshot["employer"],
                snapshot["title"],
                snapshot.get("location"),
                snapshot["retrieved_at"],
                snapshot["status"],
                source_type,
                snapshot.get("snapshot_completeness") or snapshot.get("source_digest_scope"),
                None if qualifying is None else int(bool(qualifying)),
                source_snapshot,
                actual_digest,
                source_digest,
                int(actual_digest == source_digest),
                source_artifact_id,
                now,
                revision_hash,
            ),
        )
        connection.execute(
            """INSERT OR IGNORE INTO role_jd_evidence
               (role_pack_version_id, jd_evidence_id, evidence_scope, provenance_note)
               VALUES (?, ?, 'jd_dependent', ?)""",
            (role_pack_version_id, evidence_id, f"{snapshot_id} from retained candidate evidence"),
        )
    return evidence_ids, snapshot_ids


def _insert_career_card_claims(
    connection: sqlite3.Connection,
    card_version_id: str,
    card: dict[str, Any],
    evidence_ids: list[str],
) -> None:
    claim_groups = {
        "stable_responsibility": ("stable_responsibilities", card["stable_responsibilities"]),
        "typical_deliverable": ("typical_deliverables", card["typical_deliverables"]),
        "entry_requirement": ("entry_requirements", card["entry_requirements"]),
        "transferable_direct": ("transferability/direct", card["transferability"]["direct"]),
        "transferable": ("transferability/transferable", card["transferability"]["transferable"]),
        "transferable_partial": ("transferability/partial", card["transferability"]["partial"]),
        "explicit_gap": ("transferability/gaps", card["transferability"]["gaps"]),
        "jd_dependent_scope": ("jd_dependent_scope", card["jd_dependent_scope"]),
        "validation_action": ("validation_actions", card["validation_actions"]),
    }
    for claim_kind, (json_path, texts) in claim_groups.items():
        for ordinal, claim_text in enumerate(texts):
            claim_id = stable_id("career-card-claim", card_version_id, claim_kind, claim_text)
            connection.execute(
                """INSERT OR IGNORE INTO career_card_claims
                   (career_card_claim_id, career_card_version_id, claim_kind, claim_text, provenance_path)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    claim_id,
                    card_version_id,
                    claim_kind,
                    claim_text,
                    f"data/career_cards/{card['career_card_id']}.{card['version']}.json#/{json_path}/{ordinal}",
                ),
            )
            for evidence_id in evidence_ids:
                connection.execute(
                    """INSERT OR IGNORE INTO career_card_claim_jd_evidence
                       (career_card_claim_id, jd_evidence_id) VALUES (?, ?)""",
                    (claim_id, evidence_id),
                )


def _import_career_card_match_rules(
    connection: sqlite3.Connection,
    raw: bytes,
    registry: dict[str, Any],
    now: str,
    source_path: Path,
) -> list[tuple[str, str]]:
    if registry.get("schema_version") != "career-card-match-rules-v1":
        raise ValueError("Invalid career-card match-rules schema version")
    relative_path = source_path.relative_to(ROOT).as_posix()
    content_hash = sha256(raw)
    artifact_id = stable_id("artifact", relative_path, content_hash)
    insert_or_ignore(
        connection,
        """INSERT OR IGNORE INTO source_artifacts
           (artifact_id, relative_path, content_sha256, raw_content, imported_at)
           VALUES (?, ?, ?, ?, ?)""",
        (artifact_id, relative_path, content_hash, raw.decode("utf-8"), now),
    )
    selected_rules = {}
    for rule in registry["rules"]:
        card_row = connection.execute(
            """SELECT c.career_card_version_id, v.external_key
               FROM career_cards c JOIN role_pack_versions v ON v.role_pack_version_id = c.role_pack_version_id
               WHERE c.career_card_id = ? AND c.is_current = 1 AND v.is_current = 1""",
            (rule["career_card_id"],),
        ).fetchone()
        if card_row is None:
            raise ValueError(f"Match rule {rule['rule_key']} references no current career card")
        card_version_id, role_pack = card_row
        if role_pack != rule["role_pack"]:
            raise ValueError(f"Match rule {rule['rule_key']} Role Pack does not match its career card")

        claim_id: str | None = None
        if "claim" in rule:
            claim_row = connection.execute(
                """SELECT career_card_claim_id FROM career_card_claims
                   WHERE career_card_version_id = ? AND claim_kind = ? AND claim_text = ?""",
                (card_version_id, rule["claim"]["kind"], rule["claim"]["text"]),
            ).fetchone()
            if claim_row is None:
                raise ValueError(f"Match rule {rule['rule_key']} references no matching career-card claim")
            claim_id = claim_row[0]

        negative_mapping_text = rule.get("negative_mapping_text")
        if negative_mapping_text:
            negative_row = connection.execute(
                """SELECT 1 FROM negative_mappings n
                   JOIN role_pack_versions v ON v.role_pack_version_id = n.role_pack_version_id
                   WHERE v.external_key = ? AND v.is_current = 1
                     AND n.mapping_kind = 'forbidden_claim' AND n.mapping_text = ?""",
                (role_pack, negative_mapping_text),
            ).fetchone()
            if negative_row is None:
                raise ValueError(f"Match rule {rule['rule_key']} references no Role Pack negative mapping")

        rule_hash = content_digest(rule)
        rule_id = stable_id("career-card-match-rule", card_version_id, rule["rule_key"], rule_hash)
        selected_rules[(rule["career_card_id"], rule["rule_key"])] = rule_id
        connection.execute(
            """INSERT OR IGNORE INTO career_card_match_rules
               (career_card_match_rule_id, career_card_version_id, career_card_claim_id, rule_key,
                classification, match_mode, required_capability_codes_json, allowed_scopes_json,
                negative_mapping_text, explanation, artifact_id, imported_at,
                career_card_id, content_sha256, rule_json, lifecycle_status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'superseded')""",
            (
                rule_id,
                card_version_id,
                claim_id,
                rule["rule_key"],
                rule["classification"],
                rule["match_mode"],
                json.dumps(rule["required_capability_codes"], ensure_ascii=False, sort_keys=True),
                json.dumps(rule["allowed_scopes"], ensure_ascii=False, sort_keys=True),
                negative_mapping_text,
                rule["explanation"],
                artifact_id,
                now,
                rule["career_card_id"],
                rule_hash,
                canonical_json(rule),
            ),
        )

    return activate_rules(connection, selected_rules, now)


def _import_direction_registry(
    connection: sqlite3.Connection,
    raw: bytes,
    registry: dict[str, Any],
    now: str,
    source_path: Path,
) -> None:
    relative_path = source_path.relative_to(ROOT).as_posix()
    content_hash = sha256(raw)
    artifact_id = stable_id("artifact", relative_path, content_hash)
    insert_or_ignore(
        connection,
        """INSERT OR IGNORE INTO source_artifacts
           (artifact_id, relative_path, content_sha256, raw_content, imported_at)
           VALUES (?, ?, ?, ?, ?)""",
        (artifact_id, relative_path, content_hash, raw.decode("utf-8"), now),
    )

    # These are current-only projections. Historical assignments remain in the
    # immutable registry artifact referenced by each knowledge manifest.
    for table in ("role_ecosystems", "role_lifecycle_stages", "role_function_families",
                  "career_direction_ecosystems", "career_direction_lifecycle_stages", "career_direction_function_families"):
        connection.execute(f"DELETE FROM {table}")
    for table in ("ecosystems", "lifecycle_stages", "function_families"):
        connection.execute(f"DELETE FROM {table}")
    connection.execute("UPDATE career_directions SET deprecated_at = COALESCE(deprecated_at, ?), runtime_status = 'deprecated'", (now,))

    dimension_tables = {
        "ecosystems": ("ecosystems", "ecosystem_id"),
        "lifecycle_stages": ("lifecycle_stages", "lifecycle_stage_id"),
        "function_families": ("function_families", "function_family_id"),
    }
    dimension_ids: dict[str, dict[str, str]] = {}
    for registry_key, (table, id_column) in dimension_tables.items():
        dimension_ids[registry_key] = {}
        for item in registry["taxonomy"][registry_key]:
            identifier = stable_id(table, item["code"])
            connection.execute(
                f"""INSERT INTO {table} ({id_column}, code, label, created_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(code) DO UPDATE SET label = excluded.label""",
                (identifier, item["code"], item["label"], now),
            )
            dimension_ids[registry_key][item["code"]] = identifier

    for assignment in registry["canonical_role_pack_taxonomy"]:
        row = connection.execute(
            "SELECT role_pack_version_id FROM role_pack_versions WHERE external_key = ? AND is_current = 1",
            (assignment["role_pack"],),
        ).fetchone()
        if row is None:
            raise ValueError(f"No current Role Pack version for taxonomy assignment {assignment['role_pack']}")
        _insert_role_taxonomy(connection, row[0], assignment, dimension_ids)

    for direction in registry["jd_driven_directions"]:
        _upsert_career_direction(
            connection,
            direction,
            knowledge_maturity="research",
            service_mode="jd_driven",
            requires_specific_jd=True,
            content_hash=content_hash,
            relative_path=relative_path,
            now=now,
            dimension_ids=dimension_ids,
        )
    for direction in registry["beta_directions"]:
        _upsert_career_direction(
            connection,
            direction,
            knowledge_maturity="beta",
            service_mode="explore_only",
            requires_specific_jd=False,
            content_hash=content_hash,
            relative_path=relative_path,
            now=now,
            dimension_ids=dimension_ids,
        )


def _insert_role_taxonomy(
    connection: sqlite3.Connection,
    role_pack_version_id: str,
    assignment: dict[str, Any],
    dimension_ids: dict[str, dict[str, str]],
) -> None:
    relationships = (
        ("ecosystems", "role_ecosystems", "ecosystem_id"),
        ("lifecycle_stages", "role_lifecycle_stages", "lifecycle_stage_id"),
        ("function_families", "role_function_families", "function_family_id"),
    )
    for registry_key, table, id_column in relationships:
        for code in assignment[registry_key]:
            if code not in dimension_ids[registry_key]:
                raise ValueError(f"Unknown {registry_key} taxonomy code: {code}")
            connection.execute(
                f"""INSERT OR IGNORE INTO {table} (role_pack_version_id, {id_column}, provenance_note)
                    VALUES (?, ?, ?)""",
                (role_pack_version_id, dimension_ids[registry_key][code], "data/career-map/directions-v1.json"),
            )


def _upsert_career_direction(
    connection: sqlite3.Connection,
    direction: dict[str, Any],
    *,
    knowledge_maturity: str,
    service_mode: str,
    requires_specific_jd: bool,
    content_hash: str,
    relative_path: str,
    now: str,
    dimension_ids: dict[str, dict[str, str]],
) -> None:
    required = {"external_key", "label", "summary", "boundary_note", "ecosystems", "lifecycle_stages", "function_families"}
    missing = required - direction.keys()
    if missing:
        raise ValueError(f"Invalid career direction {direction.get('external_key', '<unknown>')}; missing={sorted(missing)}")
    direction_id = stable_id("career-direction", direction["external_key"])
    connection.execute(
        """INSERT INTO career_directions
           (career_direction_id, external_key, label, knowledge_maturity, service_mode, runtime_status,
            requires_specific_jd, summary, boundary_note, source_path, source_sha256, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, 'not_routable', ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(external_key) DO UPDATE SET label = excluded.label,
               knowledge_maturity = excluded.knowledge_maturity, service_mode = excluded.service_mode,
               requires_specific_jd = excluded.requires_specific_jd, summary = excluded.summary,
               boundary_note = excluded.boundary_note, source_path = excluded.source_path,
               source_sha256 = excluded.source_sha256, updated_at = excluded.updated_at,
               deprecated_at = NULL, runtime_status = excluded.runtime_status""",
        (
            direction_id,
            direction["external_key"],
            direction["label"],
            knowledge_maturity,
            service_mode,
            int(requires_specific_jd),
            direction["summary"],
            direction["boundary_note"],
            relative_path,
            content_hash,
            now,
            now,
        ),
    )
    relationships = (
        ("ecosystems", "career_direction_ecosystems", "ecosystem_id"),
        ("lifecycle_stages", "career_direction_lifecycle_stages", "lifecycle_stage_id"),
        ("function_families", "career_direction_function_families", "function_family_id"),
    )
    for registry_key, table, id_column in relationships:
        for code in direction[registry_key]:
            if code not in dimension_ids[registry_key]:
                raise ValueError(f"Unknown {registry_key} taxonomy code: {code}")
            connection.execute(
                f"INSERT OR IGNORE INTO {table} (career_direction_id, {id_column}) VALUES (?, ?)",
                (direction_id, dimension_ids[registry_key][code]),
            )


def _insert_projection_rows(connection: sqlite3.Connection, version_id: str, pack: dict[str, Any]) -> None:
    key = pack["role_pack"]
    for rank, capability_code in enumerate(pack["priorities"], start=1):
        skill_id = stable_id("skill", capability_code)
        mapping_label, placement_hint = pack["value_mappings"][capability_code]
        connection.execute(
            """INSERT OR IGNORE INTO skills (skill_id, code, label, skill_kind, created_at)
               VALUES (?, ?, ?, 'capability_category', ?)""",
            (skill_id, capability_code, capability_code, utc_now()),
        )
        connection.execute(
            """INSERT OR IGNORE INTO role_skills
               (role_skill_id, role_pack_version_id, skill_id, priority_rank, mapping_label, placement_hint, provenance_path)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                stable_id("role-skill", version_id, capability_code),
                version_id,
                skill_id,
                rank,
                mapping_label,
                placement_hint,
                f"data/role-packs/{key}.json#/value_mappings/{capability_code}",
            ),
        )

    for evidence_kind, requirement_texts in pack["required_evidence"].items():
        for requirement_text in requirement_texts:
            connection.execute(
                """INSERT OR IGNORE INTO role_requirements
                   (role_requirement_id, role_pack_version_id, requirement_kind, requirement_text, provenance_path)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    stable_id("role-requirement", version_id, evidence_kind, requirement_text),
                    version_id,
                    evidence_kind,
                    requirement_text,
                    f"data/role-packs/{key}.json#/required_evidence/{evidence_kind}",
                ),
            )

    negative_rows = [("boundary_note", pack["skill_reference"]["boundary_note"])]
    negative_rows += [("restricted_verb", text) for text in pack["restricted_verbs"]]
    negative_rows += [("forbidden_claim", text) for text in pack["forbidden_claims"]]
    for mapping_kind, mapping_text in negative_rows:
        connection.execute(
            """INSERT OR IGNORE INTO negative_mappings
               (negative_mapping_id, role_pack_version_id, mapping_kind, mapping_text, provenance_path)
               VALUES (?, ?, ?, ?, ?)""",
            (
                stable_id("negative-mapping", version_id, mapping_kind, mapping_text),
                version_id,
                mapping_kind,
                mapping_text,
                f"data/role-packs/{key}.json#/{mapping_kind}",
            ),
        )

    policy_rows = [("preferred_action", text) for text in pack["preferred_actions"]]
    policy_rows += [("allowed_verb", text) for text in pack["allowed_verbs"]]
    policy_rows += [("sentence_pattern", text) for text in pack["sentence_patterns"]]
    for policy_kind, policy_text in policy_rows:
        connection.execute(
            """INSERT OR IGNORE INTO role_expression_policies
               (role_expression_policy_id, role_pack_version_id, policy_kind, policy_text, provenance_path)
               VALUES (?, ?, ?, ?, ?)""",
            (
                stable_id("expression-policy", version_id, policy_kind, policy_text),
                version_id,
                policy_kind,
                policy_text,
                f"data/role-packs/{key}.json#/{policy_kind}",
            ),
        )

    for ordinal, case in enumerate(pack["evaluation_cases"], start=1):
        connection.execute(
            """INSERT OR IGNORE INTO role_pack_evaluation_cases
               (evaluation_case_id, role_pack_version_id, case_ordinal, input_json, expected_output_json, provenance_path)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                stable_id("evaluation-case", version_id, str(ordinal)),
                version_id,
                ordinal,
                json.dumps(case["input"], ensure_ascii=False, sort_keys=True),
                json.dumps(case["expected_output"], ensure_ascii=False),
                f"data/role-packs/{key}.json#/evaluation_cases/{ordinal - 1}",
            ),
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True, help="SQLite database path to create or update")
    parser.add_argument("--pack-dir", type=Path, default=PACK_DIR, help="Role Pack directory (default: repository canonical source)")
    args = parser.parse_args(argv)
    result = import_packs(args.database, args.pack_dir)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
