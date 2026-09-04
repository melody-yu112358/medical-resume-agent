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


ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = ROOT / "data" / "role-packs"
SCHEMA_PATH = ROOT / "schemas" / "role-pack.schema.json"
DDL_PATH = ROOT / "database" / "career_map_schema.sql"
CAREER_MAP_DIRECTIONS_PATH = ROOT / "data" / "career-map" / "directions-v1.json"
CAREER_CARD_DIR = ROOT / "data" / "career_cards"
CAREER_CARD_SCHEMA_PATH = ROOT / "schemas" / "career-card.schema.json"
IMPORTER_VERSION = "career-map-import-v2"
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


def source_digest(packs: list[tuple[Path, bytes, dict[str, Any]]], pack_dir: Path) -> str:
    hasher = hashlib.sha256()
    for path, raw, _ in packs:
        hasher.update(path.relative_to(pack_dir).as_posix().encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(raw.replace(b"\r\n", b"\n"))
        hasher.update(b"\0")
    return hasher.hexdigest()


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
) -> dict[str, int]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    career_card_schema = json.loads(CAREER_CARD_SCHEMA_PATH.read_text(encoding="utf-8"))
    packs = load_packs(pack_dir)
    for _, _, pack in packs:
        validate_pack(pack, schema)
    directions_raw, directions = load_direction_registry(directions_path)
    career_cards = load_career_cards(career_card_dir)
    for _, _, card in career_cards:
        validate_career_card(card, career_card_schema)
    canonical_keys = {pack["role_pack"] for _, _, pack in packs}
    taxonomy_keys = {item["role_pack"] for item in directions["canonical_role_pack_taxonomy"]}
    if canonical_keys != taxonomy_keys:
        raise ValueError("Career-map taxonomy must classify exactly the current canonical Role Pack set")

    database_path.parent.mkdir(parents=True, exist_ok=True)
    now = utc_now()
    digest = source_digest(packs, pack_dir)
    import_id = stable_id("import", str(pack_dir.resolve()), digest)
    schema_version = schema["x_schema_version"]

    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(DDL_PATH.read_text(encoding="utf-8"))
        insert_or_ignore(
            connection,
            """INSERT OR IGNORE INTO import_batches
               (import_id, source_root, source_digest_sha256, imported_at, importer_version)
               VALUES (?, ?, ?, ?, ?)""",
            (import_id, str(pack_dir.resolve()), digest, now, IMPORTER_VERSION),
        )

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
                    "UPDATE role_pack_versions SET is_current = 0, superseded_by_version_id = ? "
                    "WHERE external_key = ? AND is_current = 1",
                    (version_id, pack_key),
                )
                connection.execute(
                    """INSERT INTO role_pack_versions
                       (role_pack_version_id, role_id, external_key, version_label, label, target_scope,
                        boundary_note, schema_version, content_sha256, artifact_id, is_current, imported_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)""",
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
                connection.execute(
                    "UPDATE role_pack_versions SET is_current = 0 WHERE external_key = ?",
                    (pack_key,),
                )
                connection.execute(
                    "UPDATE role_pack_versions SET is_current = 1 WHERE role_pack_version_id = ?",
                    (version_id,),
                )

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

        _import_direction_registry(connection, directions_raw, directions, now, directions_path)
        _import_career_cards(connection, career_cards, now)

    return {
        "role_packs": len(packs),
        "jd_driven_directions": len(directions["jd_driven_directions"]),
        "career_cards": len(career_cards),
        "new_versions": imported_versions,
        "source_digest": digest,
    }


def _import_career_cards(
    connection: sqlite3.Connection,
    career_cards: list[tuple[Path, bytes, dict[str, Any]]],
    now: str,
) -> None:
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
        candidate_raw = candidate_path.read_bytes()
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

        evidence_ids = _import_jd_snapshots(
            connection,
            role_row[0],
            snapshots,
            selected_ids,
            candidate_artifact_id,
            now,
        )
        card_version_id = stable_id("career-card-version", card["career_card_id"], card_hash)
        existing = connection.execute(
            "SELECT career_card_version_id FROM career_cards WHERE career_card_id = ? AND content_sha256 = ?",
            (card["career_card_id"], card_hash),
        ).fetchone()
        if existing is None:
            connection.execute(
                "UPDATE career_cards SET is_current = 0, superseded_by_version_id = ? "
                "WHERE career_card_id = ? AND is_current = 1",
                (card_version_id, card["career_card_id"]),
            )
            connection.execute(
                """INSERT INTO career_cards
                   (career_card_version_id, role_pack_version_id, career_card_id, version_label, summary,
                    scope_note, content_sha256, artifact_id, is_current, imported_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)""",
                (
                    card_version_id,
                    role_row[0],
                    card["career_card_id"],
                    card["version"],
                    card["summary"],
                    card["scope_note"],
                    card_hash,
                    card_artifact_id,
                    now,
                ),
            )
        else:
            card_version_id = existing[0]
            connection.execute("UPDATE career_cards SET is_current = 0 WHERE career_card_id = ?", (card["career_card_id"],))
            connection.execute("UPDATE career_cards SET is_current = 1 WHERE career_card_version_id = ?", (card_version_id,))
        _insert_career_card_claims(connection, card_version_id, card, evidence_ids)


def _import_jd_snapshots(
    connection: sqlite3.Connection,
    role_pack_version_id: str,
    snapshots: dict[str, dict[str, Any]],
    selected_ids: list[str],
    source_artifact_id: str,
    now: str,
) -> list[str]:
    evidence_ids: list[str] = []
    for snapshot_id in selected_ids:
        snapshot = snapshots[snapshot_id]
        source_snapshot = snapshot.get("source_snapshot")
        source_digest = snapshot.get("source_digest")
        required = ("employer", "title", "url", "retrieved_at", "status", "source_type")
        missing = [key for key in required if not snapshot.get(key)]
        if missing or not source_snapshot or not source_digest:
            raise ValueError(f"JD snapshot {snapshot_id} is incomplete; missing={missing}")
        actual_digest = sha256(source_snapshot.encode("utf-8"))
        # Older frozen evidence may define source_digest over a broader retained
        # capture than the visible excerpt. Preserve both values rather than
        # silently replacing the declared provenance or discarding the record.
        evidence_id = stable_id("jd-evidence", snapshot["url"], actual_digest)
        evidence_ids.append(evidence_id)
        connection.execute(
            """INSERT OR IGNORE INTO jd_evidence
               (jd_evidence_id, source_title, source_url, publisher, published_at, accessed_at, market,
                snapshot_sha256, source_status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, 'China', ?, 'reviewed', ?)""",
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
        snapshot_row_id = stable_id("jd-evidence-snapshot", evidence_id, snapshot_id, actual_digest)
        qualifying = snapshot.get("qualifying")
        connection.execute(
            """INSERT OR IGNORE INTO jd_evidence_snapshots
               (jd_evidence_snapshot_id, jd_evidence_id, external_snapshot_id, employer, job_title, location,
                retrieved_at, status, source_type, snapshot_completeness, qualifying, source_snapshot,
                source_digest_sha256, declared_source_digest_sha256, source_digest_matches, source_artifact_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                snapshot_row_id,
                evidence_id,
                snapshot_id,
                snapshot["employer"],
                snapshot["title"],
                snapshot.get("location"),
                snapshot["retrieved_at"],
                snapshot["status"],
                snapshot["source_type"],
                snapshot.get("snapshot_completeness"),
                None if qualifying is None else int(bool(qualifying)),
                source_snapshot,
                actual_digest,
                source_digest,
                int(actual_digest == source_digest),
                source_artifact_id,
                now,
            ),
        )
        connection.execute(
            """INSERT OR IGNORE INTO role_jd_evidence
               (role_pack_version_id, jd_evidence_id, evidence_scope, provenance_note)
               VALUES (?, ?, 'jd_dependent', ?)""",
            (role_pack_version_id, evidence_id, f"{snapshot_id} from retained candidate evidence"),
        )
    return evidence_ids


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
               source_sha256 = excluded.source_sha256, updated_at = excluded.updated_at""",
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
