#!/usr/bin/env python3
"""Generate standalone Skill role-pack references from canonical role-pack JSON."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = ROOT / "data" / "role-packs"
SCHEMA_PATH = ROOT / "schemas" / "role-pack.schema.json"
SKILL_REFERENCE_DIR = ROOT / "skill-lite" / "medical-resume-skill" / "references"
MARKDOWN_PATH = SKILL_REFERENCE_DIR / "role-packs.md"
RULES_PATH = SKILL_REFERENCE_DIR / "role-pack-rules.json"
EXECUTION_FIELDS = (
    "role_pack",
    "label",
    "priorities",
    "value_mappings",
    "preferred_actions",
    "allowed_verbs",
    "restricted_verbs",
    "forbidden_claims",
    "required_evidence",
    "sentence_patterns",
    "evaluation_cases",
)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _digestable_file_bytes(path: Path) -> bytes:
    """Use Git's LF text representation so generated metadata is cross-platform."""
    return path.read_bytes().replace(b"\r\n", b"\n")


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def load_canonical_packs() -> tuple[list[dict], dict]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    packs = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(PACK_DIR.glob("*.json"))]
    return packs, schema


def execution_projection(pack: dict) -> dict:
    return {field: pack[field] for field in EXECUTION_FIELDS}


def source_metadata(packs: list[dict], schema: dict) -> dict:
    source_hasher = hashlib.sha256()
    for path in sorted(PACK_DIR.glob("*.json")):
        source_hasher.update(path.name.encode("utf-8"))
        source_hasher.update(b"\0")
        source_hasher.update(_digestable_file_bytes(path))
        source_hasher.update(b"\0")
    return {
        "canonical_pack_versions": [pack["role_pack"] for pack in packs],
        "schema_id": schema["$id"],
        "schema_version": schema["x_schema_version"],
        "schema_sha256": _sha256_bytes(_digestable_file_bytes(SCHEMA_PATH)),
        "source_digest_sha256": source_hasher.hexdigest(),
    }


def render_markdown(packs: list[dict], metadata: dict) -> str:
    lines = [
        "<!-- GENERATED FILE — DO NOT EDIT MANUALLY.",
        "Source: data/role-packs/*.json",
        f"Canonical packs: {', '.join(metadata['canonical_pack_versions'])}",
        f"Schema: {metadata['schema_version']} ({metadata['schema_id']})",
        f"Schema SHA-256: {metadata['schema_sha256']}",
        f"Source digest SHA-256: {metadata['source_digest_sha256']} -->",
        "",
        "# Target paths",
        "",
        "This reference is generated from the canonical Role Pack configuration. "
        "A target changes the ordering and emphasis of confirmed facts; it never adds facts or upgrades responsibility.",
    ]
    for pack in packs:
        reference = pack["skill_reference"]
        lines.extend([
            "",
            f"## {pack['label']} (`{pack['role_pack']}`)",
            "",
            reference["target_scope"],
            "",
            "### Prioritize",
            "",
            *[f"- {item}" for item in reference["emphasis"]],
            "",
            "### Role-pack boundary",
            "",
            reference["boundary_note"],
            "",
            "### Execution guardrails",
            "",
            f"- Restricted wording: {'、'.join(pack['restricted_verbs']) or 'none'}.",
            f"- Forbidden claims: {'、'.join(pack['forbidden_claims']) or 'none'}.",
        ])
    return "\n".join(lines) + "\n"


def render_rules(packs: list[dict], metadata: dict) -> str:
    rules = {
        "schema_version": "medical-resume-skill-role-pack-rules-v1",
        "generated_from": metadata,
        "role_packs": [
            {
                "role_pack": pack["role_pack"],
                "label": pack["label"],
                "skill_reference": pack["skill_reference"],
                "execution_projection_sha256": _sha256_bytes(
                    _canonical_json(execution_projection(pack)).encode("utf-8")
                ),
                "restricted_verbs": pack["restricted_verbs"],
                "forbidden_claims": pack["forbidden_claims"],
                "required_evidence": pack["required_evidence"],
            }
            for pack in packs
        ],
    }
    return json.dumps(rules, ensure_ascii=False, indent=2) + "\n"


def generated_outputs() -> dict[Path, str]:
    packs, schema = load_canonical_packs()
    metadata = source_metadata(packs, schema)
    return {
        MARKDOWN_PATH: render_markdown(packs, metadata),
        RULES_PATH: render_rules(packs, metadata),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail when generated files are stale")
    args = parser.parse_args()
    outputs = generated_outputs()
    stale = [path for path, content in outputs.items() if not path.exists() or path.read_text(encoding="utf-8") != content]
    if args.check:
        if stale:
            for path in stale:
                print(f"stale generated artifact: {path.relative_to(ROOT)}")
            return 1
        print("generated role-pack references are current")
        return 0
    for path, content in outputs.items():
        path.write_text(content, encoding="utf-8")
        print(f"generated {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
