import hashlib
import json
import sqlite3
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from import_role_packs_to_career_map import import_packs  # noqa: E402


def test_role_pack_import_is_schema_valid_idempotent_and_traceable(tmp_path):
    database_path = tmp_path / "career-map.sqlite"

    first = import_packs(database_path)
    second = import_packs(database_path)

    assert first["role_packs"] == 10
    assert first["new_versions"] == 10
    assert second["role_packs"] == 10
    assert second["new_versions"] == 0

    with sqlite3.connect(database_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM roles").fetchone()[0] == 10
        assert connection.execute("SELECT COUNT(*) FROM role_pack_versions WHERE is_current = 1").fetchone()[0] == 10
        assert connection.execute("SELECT COUNT(*) FROM source_artifacts").fetchone()[0] == 10
        assert connection.execute("SELECT COUNT(*) FROM role_status_history WHERE maturity_status = 'canonical_v1'").fetchone()[0] == 10
        assert connection.execute("SELECT COUNT(*) FROM role_deliverables").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM jd_evidence").fetchone()[0] == 0

        external_key, content_hash, raw_content = connection.execute(
            """SELECT v.external_key, v.content_sha256, a.raw_content
               FROM role_pack_versions v JOIN source_artifacts a ON a.artifact_id = v.artifact_id
               WHERE v.external_key = 'regulatory_medical_writing_v1'"""
        ).fetchone()
        assert external_key == "regulatory_medical_writing_v1"
        assert content_hash == hashlib.sha256(raw_content.encode("utf-8")).hexdigest()
        assert json.loads(raw_content)["role_pack"] == external_key


def test_career_map_documentation_tracks_current_canonical_json_set():
    pack_ids = {
        json.loads(path.read_text(encoding="utf-8"))["role_pack"]
        for path in (ROOT / "data" / "role-packs").glob("*.json")
    }
    assert len(pack_ids) == 10

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    landscape = (ROOT / "docs" / "CAREER_ROLE_PACK_LANDSCAPE.md").read_text(encoding="utf-8")
    database_doc = (ROOT / "docs" / "CAREER_MAP_DATABASE.md").read_text(encoding="utf-8")

    assert "10 个" in readme
    assert "PV）保留为 Candidate" not in readme
    assert "PV，Candidate" not in landscape
    for pack_id in pack_ids:
        assert pack_id in landscape
    assert "当前 canonical source 共 10 个" in database_doc
