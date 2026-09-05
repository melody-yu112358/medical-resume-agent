"""Synthetic-only explanations bound to an immutable knowledge snapshot.

Classification is deterministic. Public JD research is never personal evidence.
"""
from __future__ import annotations

from contextlib import closing
import json
import hashlib
import sqlite3
from pathlib import Path
from typing import Any

from .career_explanation_contract import (
    EXPLANATION_CLASSES, QUERY_VERSION, digest, evaluate, interpreter_fingerprint,
    validate_capabilities, validate_rule, validate_schema,
)


class CareerCardExplanationService:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)

    def explain(self, *, profile: dict[str, Any], role_pack: str,
                knowledge_snapshot_id: str | None = None,
                jd_context: dict[str, Any] | None = None) -> dict[str, Any]:
        with closing(sqlite3.connect(f"{self.database_path.resolve().as_uri()}?mode=ro", uri=True)) as connection:
            connection.row_factory = sqlite3.Row
            connection.execute("BEGIN")
            snapshot_id, manifest = self._snapshot(connection, knowledge_snapshot_id)
            contracts = {key: self._artifact(connection, identifier)
                         for key, identifier in manifest["explanation_contracts"].items()}
            validate_schema(profile, contracts["profile_schema"], "profile")
            validate_capabilities(profile, contracts["capabilities"])
            context, card_revision = self._context(connection, manifest, role_pack)
            rule_refs = [item for item in manifest["match_rule_revisions"]
                         if item["career_card_version_id"] == card_revision]
            if not rule_refs:
                raise LookupError(f"no explanation match rules for {role_pack}")
            rules = []
            for reference in rule_refs:
                row = connection.execute("""SELECT r.*, c.claim_kind, c.claim_text
                    FROM career_card_match_rules r JOIN career_card_claims c
                    ON c.career_card_claim_id = r.career_card_claim_id
                    WHERE r.career_card_match_rule_id = ? AND r.career_card_version_id = ?""",
                    (reference["career_card_match_rule_id"], card_revision)).fetchone()
                if row is None:
                    raise LookupError("snapshot rule or claim revision is unavailable")
                rule = json.loads(row["rule_json"])
                validate_schema({"schema_version": "career-card-match-rules-v2", "rules": [rule]}, contracts["rule_schema"], "match rule")
                validate_rule(rule, contracts["capabilities"])
                if digest(rule) != reference["content_sha256"] or rule["claim"] != {"kind": row["claim_kind"], "text": row["claim_text"]}:
                    raise ValueError("snapshot rule / claim integrity mismatch")
                rules.append((row, rule))
            source_refs = {item["jd_evidence_snapshot_id"]: item for item in manifest["jd_snapshot_revisions"]
                           if item["career_card_version_id"] == card_revision}
            applicable_keys, seniority, jd_usable = None, None, True
            if jd_context is not None:
                validate_schema(jd_context, contracts["jd_context_schema"], "JD context")
                applicable_keys = set(jd_context["applicable_rule_keys"])
                if applicable_keys - {rule["rule_key"] for _, rule in rules}:
                    raise ValueError("JD context references an unknown target rule")
                if set(jd_context["jd_evidence_snapshot_ids"]) - source_refs.keys():
                    raise ValueError("JD context references a snapshot outside the selected target knowledge snapshot")
                seniority = jd_context.get("seniority")
                jd_usable = all(self._source_status(source_refs[key])["usable"] for key in jd_context["jd_evidence_snapshot_ids"])
            input_digest = digest({"profile": profile, "role_pack": role_pack, "jd_context": jd_context})
            explanations = {label: [] for label in EXPLANATION_CLASSES}
            items = []
            for row, rule in sorted(rules, key=lambda pair: pair[1]["rule_key"]):
                result = evaluate(rule, profile["evidence"], applicable_rule_keys=applicable_keys,
                                  seniority=seniority, jd_usable=jd_usable)
                claim_id = row["career_card_claim_id"]
                boundary = self._boundary(connection, context["role_pack"]["version_id"], rule.get("negative_mapping_text"))
                sources = self._sources(connection, manifest, source_refs, claim_id)
                evidence_ids = result["profile_evidence_ids"]
                provenance = {
                    "profile_evidence_ids": evidence_ids,
                    "career_card_claim_id": claim_id,
                    "career_card_revision": card_revision,
                    "role_pack_revision": context["role_pack"]["version_id"],
                    "role_pack_boundary_id": boundary["negative_mapping_id"] if boundary else None,
                    "match_rule_revision": row["career_card_match_rule_id"],
                    "match_rule_content_sha256": row["content_sha256"],
                    "knowledge_snapshot_id": snapshot_id,
                    "jd_evidence_snapshot_ids": [item["jd_evidence_snapshot_id"] for item in sources],
                    "jd_evidence_status": [{"jd_evidence_snapshot_id": item["jd_evidence_snapshot_id"], **item["evidence_status"]} for item in sources],
                    "input_digest": input_digest,
                    "role_pack": context["role_pack"], "career_card": context["career_card"],
                    "career_card_claim": {"claim_id": claim_id, "kind": row["claim_kind"], "text": row["claim_text"]},
                    "role_pack_negative_mapping": boundary, "jd_evidence": sources,
                }
                usable_support = [item["jd_evidence_snapshot_id"] for item in sources
                                  if "claim_support" in item["relations"] and item["evidence_status"]["usable"]]
                item = {
                    "explanation_id": digest({"snapshot": snapshot_id, "rule": row["career_card_match_rule_id"], "input": input_digest}),
                    "rule_key": rule["rule_key"], **result,
                    "target_claim": provenance["career_card_claim"],
                    "boundary_target": boundary,
                    "explanation": self._text(rule, result),
                    "profile_evidence": [self._public_evidence(e) for e in profile["evidence"] if e["evidence_id"] in evidence_ids],
                    "claim_support_snapshot_ids": usable_support,
                    "source_evidence_state": "reviewed_claim_support" if usable_support else ("background_research_only" if sources else "no_sources"),
                    "provenance": provenance,
                }
                items.append(item)
                for label in result["display_labels"]:
                    explanations[label].append(item)
            return {
                "query_version": QUERY_VERSION, "knowledge_snapshot_id": snapshot_id, "input_digest": input_digest,
                "profile_id": profile["profile_id"], "profile_type": "synthetic",
                **context, "items": items, "explanations": explanations,
                "non_goals": [
                    "No percentage, ranking, employability, or success judgement is produced.",
                    "Unsupported describes a prohibited inference, not a person's suitability.",
                    "Background research sources are not claim-level support or personal evidence.",
                    "Profiles are transient and do not create runtime routing decisions.",
                ],
            }

    @staticmethod
    def _snapshot(connection, snapshot_id):
        row = connection.execute(
            "SELECT * FROM knowledge_snapshots WHERE knowledge_snapshot_id = ?" if snapshot_id else
            "SELECT * FROM knowledge_snapshots WHERE is_current = 1", (snapshot_id,) if snapshot_id else (),
        ).fetchone()
        if row is None:
            raise LookupError("knowledge snapshot is unavailable; import source files first")
        manifest = json.loads(row["manifest_json"])
        if digest(manifest) != row["manifest_sha256"]:
            raise ValueError("knowledge manifest integrity mismatch")
        interpreter = manifest["explanation_interpreter"]
        if manifest["schema_version"] != "career-map-knowledge-snapshot-v2" or interpreter != {"version": QUERY_VERSION, "source_sha256": interpreter_fingerprint()}:
            raise ValueError("incompatible historical snapshot interpreter; use its recorded interpreter version")
        return row["knowledge_snapshot_id"], manifest

    @staticmethod
    def _artifact(connection, identifier):
        row = connection.execute("SELECT raw_content, content_sha256 FROM source_artifacts WHERE artifact_id = ?", (identifier,)).fetchone()
        if row is None:
            raise LookupError("snapshot contract artifact is unavailable")
        if hashlib.sha256(row[0].encode("utf-8")).hexdigest() != row[1]:
            raise ValueError("snapshot contract artifact integrity mismatch")
        return json.loads(row[0])

    @staticmethod
    def _context(connection, manifest, role_pack):
        if not isinstance(role_pack, str):
            raise ValueError("role_pack must be a string")
        packs = [item for item in manifest["role_pack_revisions"] if item["external_key"] == role_pack]
        cards = [item for item in manifest["career_card_revisions"] if packs and item["role_pack_version_id"] == packs[0]["role_pack_version_id"]]
        if len(packs) != 1 or len(cards) != 1:
            raise LookupError(f"no unique explainable Career Card for Role Pack: {role_pack}")
        pack, card = packs[0], cards[0]
        row = connection.execute("""SELECT v.label, ra.relative_path AS pack_path, c.version_label,
            ca.relative_path AS card_path FROM career_cards c
            JOIN role_pack_versions v ON v.role_pack_version_id = c.role_pack_version_id
            JOIN source_artifacts ra ON ra.artifact_id = v.artifact_id
            JOIN source_artifacts ca ON ca.artifact_id = c.artifact_id
            WHERE c.career_card_version_id = ? AND v.role_pack_version_id = ?""",
            (card["career_card_version_id"], pack["role_pack_version_id"])).fetchone()
        if row is None:
            raise LookupError("snapshot Card or Role Pack revision unavailable")
        return {
            "role_pack": {"external_key": role_pack, "version_id": pack["role_pack_version_id"],
                          "label": row["label"], "content_sha256": pack["content_sha256"], "artifact_path": row["pack_path"]},
            "career_card": {"career_card_id": card["career_card_id"], "version_id": card["career_card_version_id"],
                            "version_label": row["version_label"], "content_sha256": card["content_sha256"], "artifact_path": row["card_path"]},
        }, card["career_card_version_id"]

    @staticmethod
    def _boundary(connection, role_revision, text):
        if not text:
            return None
        row = connection.execute("""SELECT negative_mapping_id, mapping_text AS text, provenance_path
            FROM negative_mappings WHERE role_pack_version_id = ? AND mapping_kind = 'forbidden_claim' AND mapping_text = ?""",
            (role_revision, text)).fetchone()
        if row is None:
            raise ValueError("missing Role Pack boundary")
        return dict(row)

    @staticmethod
    def _source_status(reference):
        status = reference["snapshot_status"]
        unavailable = bool(reference["snapshot_deprecated_at"] or reference["source_deprecated_at"]) or reference["source_status"] == "deprecated" or status.lower() in {"deprecated", "withdrawn", "expired", "retired"}
        return {"snapshot_status": status, "source_status": reference["source_status"],
                "usable": not unavailable and reference["source_status"] == "reviewed", "source_digest_matches": bool(reference["source_digest_matches"])}

    def _sources(self, connection, manifest, references, claim_id):
        links = [item for item in manifest["claim_evidence_links"] if item["career_card_claim_id"] == claim_id]
        sources = []
        for identifier in sorted({item["jd_evidence_snapshot_id"] for item in links}):
            if identifier not in references:
                raise ValueError("claim evidence is outside its Card revision")
            reference = references[identifier]
            row = connection.execute("""SELECT s.external_snapshot_id, j.source_url, s.retrieved_at AS accessed_at,
                s.jd_evidence_id FROM jd_evidence_snapshots s JOIN jd_evidence j ON j.jd_evidence_id = s.jd_evidence_id
                WHERE s.jd_evidence_snapshot_id = ?""", (identifier,)).fetchone()
            if row is None:
                raise LookupError("JD snapshot unavailable")
            related = [link for link in links if link["jd_evidence_snapshot_id"] == identifier]
            sources.append({**dict(row), "jd_evidence_snapshot_id": identifier,
                            "relations": sorted(link["relation_kind"] for link in related),
                            "research_source_label": "background research source",
                            "claim_support_reviews": [link for link in related if link["relation_kind"] == "claim_support"],
                            "source_digest_sha256": reference["source_digest_sha256"],
                            "declared_source_digest_sha256": reference["declared_source_digest_sha256"],
                            "evidence_status": self._source_status(reference)})
        return sources

    @staticmethod
    def _public_evidence(item):
        return {key: item[key] for key in ("evidence_id", "statement", "capability_codes", "scope")}

    @staticmethod
    def _text(rule, result):
        claim = rule["claim"]["text"]
        if result["assessment_status"] != "assessed":
            return f"“{claim}”需具体且适用的 JD 上下文核验，当前不作为能力缺口。"
        if result["support_completeness"] == "no_evidence":
            return f"当前未提供支持“{claim}”的证据；不代表没有该能力或不适合该职业。"
        if result["support_completeness"] == "partial":
            suffix = f" 尚缺条件：{', '.join(result['required_missing_capability_codes'])}。" if result["required_missing_capability_codes"] else " 现有事实仅支持该 claim 的有限范围。"
            boundary = f" 不能据此推出：{rule['negative_mapping_text']}。" if rule.get("negative_mapping_text") else ""
            return f"当前证据部分支持“{claim}”。{suffix}{boundary}"
        return rule["explanation"]
