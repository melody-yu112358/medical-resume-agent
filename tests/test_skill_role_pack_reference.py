import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from medical_career_agent.services.bullet_composer import BulletComposerService
from medical_career_agent.services.claim_gate import ClaimGateService
from scripts.generate_skill_role_pack_reference import (
    EXECUTION_FIELDS,
    _canonical_json,
    execution_projection,
    generated_outputs,
    load_canonical_packs,
)


SKILL = ROOT / "skill-lite" / "medical-resume-skill"
PACK_DIR = ROOT / "data" / "role-packs"
SNAPSHOT_PATH = ROOT / "tests" / "fixtures" / "role-pack-execution-projection-v1.json"
PREEXISTING_PACKS = {
    "clinical_research_v1": "c592b53c92a1d106fa779d553f00e06c192f235055b44caa90dc13eebff2139b",
    "doctoral_v1": "5df02f35359bc09c628aaa134379ea84b5f4da2e0dd7a8ca6cf910522fae5786",
    "health_ai_data_v1": "0985af03477dbe6aa677b44da804862107de825ea4f74585a7df00d963bcb566",
    "medical_affairs_v1": "199b6e8bbffcc13a248d226309ba1d19ba127073f9c73e97cea50dc34dcd0eee",
}


def projection_digest(pack: dict) -> str:
    return hashlib.sha256(
        _canonical_json(execution_projection(pack)).encode("utf-8")
    ).hexdigest()


def test_execution_projection_matches_frozen_snapshot():
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    packs, _ = load_canonical_packs()

    assert tuple(snapshot["execution_fields"]) == EXECUTION_FIELDS
    assert {
        pack["role_pack"]: projection_digest(pack)
        for pack in packs
    } == snapshot["projections"]


def test_preexisting_role_pack_execution_projections_are_unchanged():
    packs, _ = load_canonical_packs()
    actual = {pack["role_pack"]: projection_digest(pack) for pack in packs}

    assert {name: actual[name] for name in PREEXISTING_PACKS} == PREEXISTING_PACKS


def test_real_agent_loaders_accept_metadata_without_execution_change():
    """Exercise the production JSON loaders, not merely the JSON schema."""
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))["projections"]
    composer = BulletComposerService(PACK_DIR)
    claim_gate = ClaimGateService(PACK_DIR)

    for role_pack_name, expected_digest in snapshot.items():
        composer_pack = composer._load_role_pack(role_pack_name)
        gate_pack = claim_gate._load_role_pack(role_pack_name)

        assert composer_pack["skill_reference"] == gate_pack["skill_reference"]
        assert projection_digest(composer_pack) == expected_digest
        assert projection_digest(gate_pack) == expected_digest


def test_generated_references_are_current_and_traceable():
    for path, expected in generated_outputs().items():
        assert path.read_text(encoding="utf-8") == expected

    rules = json.loads((SKILL / "references" / "role-pack-rules.json").read_text(encoding="utf-8"))
    metadata = rules["generated_from"]
    assert metadata["schema_version"] == "medical-role-pack-schema-v1"
    assert len(metadata["source_digest_sha256"]) == 64
    assert len(metadata["schema_sha256"]) == 64


def test_standalone_invariants_run_without_agent_imports(tmp_path):
    package_root = tmp_path / "medical-resume-skill"
    shutil.copytree(SKILL, package_root)
    validator = package_root / "scripts" / "validate_standalone_cases.py"

    passing = subprocess.run(
        [sys.executable, str(validator)], capture_output=True, text=True, check=False
    )
    assert passing.returncode == 0, passing.stdout + passing.stderr
    assert "standalone invariant validation passed: 4 cases" in passing.stdout

    cases_path = package_root / "references" / "standalone-eval-cases.json"
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    cases["cases"][0]["candidate_text"] += " 主导研究团队。"
    mutated_cases = tmp_path / "mutated-cases.json"
    mutated_cases.write_text(json.dumps(cases, ensure_ascii=False), encoding="utf-8")
    failing = subprocess.run(
        [sys.executable, str(validator), "--cases", str(mutated_cases)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert failing.returncode == 1
    assert "forbidden phrase 主导" in failing.stdout
