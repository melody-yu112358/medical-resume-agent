"""Transactional schema upgrade and content-addressed Career Map snapshots.

Only current projections/lifecycle pointers are mutable. Legacy rows retain
original IDs; pre-manifest history is traceable, not retroactively replayable.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import uuid
from typing import Any


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def content_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def needs_legacy_upgrade(connection: sqlite3.Connection) -> bool:
    columns = {row[1] for row in connection.execute("PRAGMA table_info(career_cards)")}
    return bool(columns) and "revision_sha256" not in columns


def apply_schema(connection: sqlite3.Connection, ddl: str, *, upgrade: bool) -> None:
    if upgrade:
        for table in ("career_cards", "jd_evidence_snapshots", "career_card_match_rules"):
            rows = [dict(zip([col[0] for col in cursor.description], row))
                    for cursor in [connection.execute(f"SELECT * FROM {table}")]
                    for row in cursor.fetchall()]
            statement = re.search(
                rf"CREATE TABLE IF NOT EXISTS {table} \([\s\S]*?\n\);", ddl
            ).group(0)
            temporary = f"{table}_revision_upgrade"
            connection.execute(statement.replace(f"EXISTS {table} (", f"EXISTS {temporary} (", 1))
            for row in rows:
                if table == "career_cards":
                    row.update(revision_sha256=content_digest({"legacy_card": row}), jd_artifact_id=None)
                elif table == "jd_evidence_snapshots":
                    row["revision_sha256"] = content_digest({"legacy_snapshot": row})
                else:
                    card = connection.execute(
                        "SELECT career_card_id, is_current FROM career_cards WHERE career_card_version_id = ?",
                        (row["career_card_version_id"],),
                    ).fetchone()
                    # Retain the exact imported rule payload, including stale legacy rules.
                    payload = {key: row[key] for key in (
                        "rule_key", "classification", "match_mode", "required_capability_codes_json",
                        "allowed_scopes_json", "negative_mapping_text", "explanation", "career_card_claim_id",
                    )}
                    row.update(
                        career_card_id=card[0], content_sha256=content_digest({"legacy_rule": payload}),
                        rule_json=canonical_json(payload), superseded_by_rule_id=None,
                        lifecycle_status="revoked" if row["deprecated_at"] else ("current" if card[1] else "superseded"),
                    )
                columns = list(row)
                connection.execute(
                    f"INSERT INTO {temporary} ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})",
                    tuple(row.values()),
                )
            connection.execute(f"DROP TABLE {table}")
            connection.execute(f"ALTER TABLE {temporary} RENAME TO {table}")

    # executescript commits a pending transaction: execute complete statements
    # individually so schema upgrades and data activation roll back together.
    pending = ""
    for line in ddl.splitlines(keepends=True):
        pending += line
        if sqlite3.complete_statement(pending):
            connection.execute(pending)
            pending = ""
    if upgrade:
        connection.execute("""INSERT OR IGNORE INTO career_card_jd_snapshots
            SELECT DISTINCT c.career_card_version_id, s.jd_evidence_snapshot_id
            FROM career_card_claims c
            JOIN career_card_claim_jd_evidence j ON j.career_card_claim_id = c.career_card_claim_id
            JOIN jd_evidence_snapshots s ON s.jd_evidence_id = j.jd_evidence_id""")
    connection.execute("PRAGMA user_version = 3")


def activate_versions(connection: sqlite3.Connection, table: str, id_column: str,
                      key_column: str, selected: dict[str, str], now: str) -> None:
    previous = connection.execute(
        f"SELECT {key_column}, {id_column} FROM {table} WHERE is_current = 1"
    ).fetchall()
    for key, old_id in previous:
        new_id = selected.get(key)
        if old_id != new_id:
            connection.execute(
                f"UPDATE {table} SET is_current = 0, superseded_by_version_id = ?, deprecated_at = ? WHERE {id_column} = ?",
                (new_id, now, old_id),
            )
    for new_id in selected.values():
        connection.execute(
            f"UPDATE {table} SET is_current = 1, superseded_by_version_id = NULL, deprecated_at = NULL WHERE {id_column} = ?",
            (new_id,),
        )


def activate_rules(connection: sqlite3.Connection, selected: dict[tuple[str, str], str],
                   now: str) -> list[tuple[str, str]]:
    changes = []
    previous = connection.execute("""SELECT career_card_id, rule_key, career_card_match_rule_id
        FROM career_card_match_rules WHERE lifecycle_status = 'current'""").fetchall()
    for card_id, key, old_id in previous:
        new_id = selected.get((card_id, key))
        if new_id != old_id:
            status = "superseded" if new_id else "revoked"
            connection.execute("""UPDATE career_card_match_rules
                SET lifecycle_status = ?, superseded_by_rule_id = ?, deprecated_at = ?
                WHERE career_card_match_rule_id = ?""", (status, new_id, now, old_id))
            changes.append((old_id, status))
    for new_id in selected.values():
        status = connection.execute("SELECT lifecycle_status FROM career_card_match_rules WHERE career_card_match_rule_id = ?", (new_id,)).fetchone()[0]
        if status != "current":
            connection.execute("""UPDATE career_card_match_rules SET lifecycle_status = 'current',
                superseded_by_rule_id = NULL, deprecated_at = NULL WHERE career_card_match_rule_id = ?""", (new_id,))
            changes.append((new_id, "current"))
    return changes


def save_snapshot(connection: sqlite3.Connection, *, sources: list[dict[str, str]],
                  taxonomy_artifact_id: str, rule_artifact_id: str, interpreter: dict[str, str],
                  importer_version: str, now: str, rule_changes: list[tuple[str, str]]) -> tuple[str, str]:
    def records(query: str) -> list[dict[str, Any]]:
        cursor = connection.execute(query)
        return [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]

    manifest = {
        "schema_version": "career-map-knowledge-snapshot-v1",
        "importer_version": importer_version,
        "explanation_interpreter": interpreter,
        "sources": sorted(sources, key=lambda item: item["path"]),
        "taxonomy_revision": taxonomy_artifact_id,
        "match_rule_registry_artifact_id": rule_artifact_id,
        "role_pack_revisions": records("""SELECT external_key, role_pack_version_id, content_sha256, artifact_id
            FROM role_pack_versions WHERE is_current = 1 ORDER BY external_key"""),
        "career_card_revisions": records("""SELECT career_card_id, career_card_version_id, role_pack_version_id,
            content_sha256, revision_sha256, artifact_id, jd_artifact_id
            FROM career_cards WHERE is_current = 1 ORDER BY career_card_id"""),
        "match_rule_revisions": records("""SELECT career_card_id, rule_key, career_card_match_rule_id,
            career_card_version_id, content_sha256 FROM career_card_match_rules
            WHERE lifecycle_status = 'current' ORDER BY career_card_id, rule_key"""),
        "jd_snapshot_revisions": records("""SELECT cs.career_card_version_id, s.jd_evidence_snapshot_id,
            s.jd_evidence_id, s.external_snapshot_id, s.revision_sha256, s.source_artifact_id,
            s.source_digest_sha256, s.declared_source_digest_sha256
            FROM career_card_jd_snapshots cs
            JOIN career_cards c ON c.career_card_version_id = cs.career_card_version_id AND c.is_current = 1
            JOIN jd_evidence_snapshots s ON s.jd_evidence_snapshot_id = cs.jd_evidence_snapshot_id
            ORDER BY cs.career_card_version_id, s.external_snapshot_id"""),
    }
    digest = content_digest(manifest)
    snapshot_id = f"knowledge-{digest}"
    connection.execute("""INSERT OR IGNORE INTO knowledge_snapshots
        (knowledge_snapshot_id, manifest_sha256, manifest_json, interpreter_version, importer_version, is_current, created_at)
        VALUES (?, ?, ?, ?, ?, 0, ?)""",
        (snapshot_id, digest, canonical_json(manifest), interpreter["version"], importer_version, now))
    previous = connection.execute("SELECT knowledge_snapshot_id FROM knowledge_snapshots WHERE is_current = 1").fetchone()
    if previous is None or previous[0] != snapshot_id:
        connection.execute("UPDATE knowledge_snapshots SET is_current = 0 WHERE is_current = 1")
        connection.execute("UPDATE knowledge_snapshots SET is_current = 1 WHERE knowledge_snapshot_id = ?", (snapshot_id,))
        connection.execute("INSERT INTO knowledge_snapshot_activations VALUES (?, ?, ?)", (str(uuid.uuid4()), snapshot_id, now))
    for rule_id, status in rule_changes:
        connection.execute("INSERT INTO career_card_match_rule_events VALUES (?, ?, ?, ?, ?)",
                           (str(uuid.uuid4()), rule_id, snapshot_id, status, now))
    return snapshot_id, digest
