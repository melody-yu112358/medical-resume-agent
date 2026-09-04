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
IMPORTER_VERSION = "career-map-import-v1"
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


def source_digest(packs: list[tuple[Path, bytes, dict[str, Any]]], pack_dir: Path) -> str:
    hasher = hashlib.sha256()
    for path, raw, _ in packs:
        hasher.update(path.relative_to(pack_dir).as_posix().encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(raw.replace(b"\r\n", b"\n"))
        hasher.update(b"\0")
    return hasher.hexdigest()


def insert_or_ignore(connection: sqlite3.Connection, statement: str, values: tuple[Any, ...]) -> None:
    connection.execute(statement, values)


def import_packs(database_path: Path, pack_dir: Path = PACK_DIR) -> dict[str, int]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    packs = load_packs(pack_dir)
    for _, _, pack in packs:
        validate_pack(pack, schema)

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

    return {"role_packs": len(packs), "new_versions": imported_versions, "source_digest": digest}


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
