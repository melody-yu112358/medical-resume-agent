"""Deterministic, score-free Career Profile to Role Card explanations.

This is intentionally separate from the legacy percentage-based comparator.
It accepts synthetic or confirmed transient evidence in memory and reads only
the rebuildable career-map SQLite projection; it does not persist profiles or
make a fit, employability, or success judgement.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


EXPLANATION_CLASSES = ("direct", "transferable", "partial", "gap", "unsupported")


class CareerCardExplanationService:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)

    def explain(self, *, profile: dict[str, Any], role_pack: str) -> dict[str, Any]:
        if profile.get("profile_type") != "synthetic":
            raise ValueError("v1 explanation queries accept synthetic profiles only")
        evidence = profile.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            raise ValueError("profile must contain evidence")
        if any(item.get("evidence_status") != "confirmed" for item in evidence):
            raise ValueError("every profile evidence item must be confirmed")

        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row
            context = self._load_context(connection, role_pack)
            rules = connection.execute(
                """SELECT r.*, c.claim_kind, c.claim_text
                   FROM career_card_match_rules r
                   LEFT JOIN career_card_claims c ON c.career_card_claim_id = r.career_card_claim_id
                   WHERE r.career_card_version_id = ? AND r.deprecated_at IS NULL
                   ORDER BY r.rule_key""",
                (context["career_card"]["version_id"],),
            ).fetchall()
            if not rules:
                raise LookupError(f"no explanation match rules for {role_pack}")

            explanations: dict[str, list[dict[str, Any]]] = {
                classification: [] for classification in EXPLANATION_CLASSES
            }
            for rule in rules:
                matched_evidence = self._matching_evidence(
                    evidence,
                    json.loads(rule["required_capability_codes_json"]),
                    json.loads(rule["allowed_scopes_json"]),
                    rule["match_mode"],
                )
                if matched_evidence is None:
                    continue
                claim = (
                    {
                        "claim_id": rule["career_card_claim_id"],
                        "kind": rule["claim_kind"],
                        "text": rule["claim_text"],
                    }
                    if rule["career_card_claim_id"]
                    else None
                )
                explanations[rule["classification"]].append(
                    {
                        "rule_key": rule["rule_key"],
                        "explanation": rule["explanation"],
                        "profile_evidence": [self._public_evidence(item) for item in matched_evidence],
                        "provenance": {
                            "role_pack": context["role_pack"],
                            "career_card": context["career_card"],
                            "career_card_claim": claim,
                            "role_pack_negative_mapping": self._negative_mapping(
                                connection, context["role_pack"]["version_id"], rule["negative_mapping_text"]
                            ),
                            "jd_evidence": self._jd_evidence(
                                connection,
                                context["role_pack"]["version_id"],
                                rule["career_card_claim_id"],
                            ),
                        },
                    }
                )

        return {
            "query_version": "career-card-explanation-v1",
            "profile_id": profile["profile_id"],
            "profile_type": "synthetic",
            "role_pack": context["role_pack"],
            "career_card": context["career_card"],
            "explanations": explanations,
            "non_goals": [
                "No percentage, fit, employability, salary, or success score is produced.",
                "The query does not persist a profile or create a runtime routing decision.",
            ],
        }

    def _load_context(self, connection: sqlite3.Connection, role_pack: str) -> dict[str, dict[str, Any]]:
        row = connection.execute(
            """SELECT v.role_pack_version_id, v.external_key, v.label, v.content_sha256 AS role_pack_sha256,
                      ra.relative_path AS role_pack_artifact_path,
                      c.career_card_version_id, c.career_card_id, c.version_label,
                      c.content_sha256 AS career_card_sha256, ca.relative_path AS career_card_artifact_path
               FROM role_pack_versions v
               JOIN source_artifacts ra ON ra.artifact_id = v.artifact_id
               JOIN career_cards c ON c.role_pack_version_id = v.role_pack_version_id AND c.is_current = 1
               JOIN source_artifacts ca ON ca.artifact_id = c.artifact_id
               WHERE v.external_key = ? AND v.is_current = 1""",
            (role_pack,),
        ).fetchone()
        if row is None:
            raise LookupError(f"no current Career Card for Role Pack: {role_pack}")
        return {
            "role_pack": {
                "external_key": row["external_key"],
                "version_id": row["role_pack_version_id"],
                "label": row["label"],
                "content_sha256": row["role_pack_sha256"],
                "artifact_path": row["role_pack_artifact_path"],
            },
            "career_card": {
                "career_card_id": row["career_card_id"],
                "version_id": row["career_card_version_id"],
                "version_label": row["version_label"],
                "content_sha256": row["career_card_sha256"],
                "artifact_path": row["career_card_artifact_path"],
            },
        }

    @staticmethod
    def _matching_evidence(
        evidence: list[dict[str, Any]],
        required_codes: list[str],
        allowed_scopes: list[str],
        match_mode: str,
    ) -> list[dict[str, Any]] | None:
        scoped = [
            item for item in evidence if not allowed_scopes or item.get("scope") in allowed_scopes
        ]
        matched = [
            item
            for item in scoped
            if set(item.get("capability_codes", [])).intersection(required_codes)
        ]
        present_codes = {
            code for item in scoped for code in item.get("capability_codes", [])
        }
        if match_mode == "all_capabilities_present":
            return matched if set(required_codes).issubset(present_codes) else None
        if match_mode == "any_capability_present":
            return matched or None
        if match_mode == "all_capabilities_absent":
            return [] if not set(required_codes).intersection(present_codes) else None
        raise ValueError(f"unsupported match mode: {match_mode}")

    @staticmethod
    def _public_evidence(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "evidence_id": item["evidence_id"],
            "statement": item["statement"],
            "capability_codes": item["capability_codes"],
            "scope": item["scope"],
        }

    @staticmethod
    def _negative_mapping(
        connection: sqlite3.Connection, role_pack_version_id: str, mapping_text: str | None
    ) -> dict[str, str] | None:
        if not mapping_text:
            return None
        row = connection.execute(
            """SELECT negative_mapping_id, mapping_text, provenance_path FROM negative_mappings
               WHERE role_pack_version_id = ? AND mapping_kind = 'forbidden_claim' AND mapping_text = ?""",
            (role_pack_version_id, mapping_text),
        ).fetchone()
        if row is None:
            raise LookupError(f"missing negative mapping: {mapping_text}")
        return {
            "negative_mapping_id": row["negative_mapping_id"],
            "text": row["mapping_text"],
            "provenance_path": row["provenance_path"],
        }

    @staticmethod
    def _jd_evidence(
        connection: sqlite3.Connection, role_pack_version_id: str, claim_id: str | None
    ) -> list[dict[str, str | None]]:
        if claim_id:
            query = """SELECT DISTINCT j.jd_evidence_id, s.external_snapshot_id, j.source_url,
                                      j.accessed_at, s.source_digest_sha256, s.declared_source_digest_sha256
                       FROM career_card_claim_jd_evidence cj
                       JOIN jd_evidence j ON j.jd_evidence_id = cj.jd_evidence_id
                       JOIN jd_evidence_snapshots s ON s.jd_evidence_id = j.jd_evidence_id
                       WHERE cj.career_card_claim_id = ?
                       ORDER BY s.external_snapshot_id"""
            values: tuple[str, ...] = (claim_id,)
        else:
            query = """SELECT DISTINCT j.jd_evidence_id, s.external_snapshot_id, j.source_url,
                                      j.accessed_at, s.source_digest_sha256, s.declared_source_digest_sha256
                       FROM role_jd_evidence r
                       JOIN jd_evidence j ON j.jd_evidence_id = r.jd_evidence_id
                       JOIN jd_evidence_snapshots s ON s.jd_evidence_id = j.jd_evidence_id
                       WHERE r.role_pack_version_id = ?
                       ORDER BY s.external_snapshot_id"""
            values = (role_pack_version_id,)
        return [dict(row) for row in connection.execute(query, values).fetchall()]
