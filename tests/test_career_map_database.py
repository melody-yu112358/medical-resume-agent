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
    assert first["career_cards"] == 5
    assert first["career_card_match_rules"] == 10
    assert first["new_versions"] == 10
    assert second["role_packs"] == 10
    assert second["new_versions"] == 0

    with sqlite3.connect(database_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM roles").fetchone()[0] == 10
        assert connection.execute("SELECT COUNT(*) FROM role_pack_versions WHERE is_current = 1").fetchone()[0] == 10
        assert connection.execute("SELECT COUNT(*) FROM source_artifacts").fetchone()[0] == 22
        assert connection.execute("SELECT COUNT(*) FROM role_status_history WHERE maturity_status = 'canonical_v1'").fetchone()[0] == 10
        assert connection.execute("SELECT COUNT(*) FROM career_directions WHERE service_mode = 'jd_driven'").fetchone()[0] == 6
        assert connection.execute("SELECT COUNT(*) FROM career_map_entries").fetchone()[0] == 16
        assert connection.execute("SELECT COUNT(*) FROM role_ecosystems").fetchone()[0] >= 10
        assert connection.execute("SELECT COUNT(*) FROM role_function_families").fetchone()[0] >= 10
        assert connection.execute("SELECT COUNT(*) FROM role_deliverables").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM career_cards WHERE is_current = 1").fetchone()[0] == 5
        assert connection.execute("SELECT COUNT(*) FROM career_card_claims").fetchone()[0] == 103
        assert connection.execute("SELECT COUNT(*) FROM jd_evidence").fetchone()[0] == 44
        assert connection.execute("SELECT COUNT(*) FROM jd_evidence_snapshots").fetchone()[0] == 44
        assert connection.execute("SELECT COUNT(*) FROM role_jd_evidence WHERE evidence_scope = 'jd_dependent'").fetchone()[0] == 44
        assert connection.execute("SELECT COUNT(*) FROM career_card_claim_jd_evidence").fetchone()[0] == 904
        assert connection.execute("SELECT COUNT(*) FROM career_card_match_rules").fetchone()[0] == 10
        assert connection.execute("SELECT COUNT(*) FROM jd_evidence_snapshots WHERE source_digest_matches = 0").fetchone()[0] == 9

        card_role_pairs = connection.execute(
            """SELECT c.career_card_id, v.external_key FROM career_cards c
               JOIN role_pack_versions v ON v.role_pack_version_id = c.role_pack_version_id
               WHERE c.is_current = 1 ORDER BY c.career_card_id"""
        ).fetchall()
        assert card_role_pairs == [
            ("clinical_data_management", "clinical_data_management_v1"),
            ("clinical_research_associate", "clinical_research_associate_v1"),
            ("medical_device_clinical_application_specialist", "medical_device_clinical_application_specialist_v1"),
            ("pharmacovigilance_drug_safety", "pharmacovigilance_drug_safety_v1"),
            ("regulatory_medical_writing", "regulatory_medical_writing_v1"),
        ]

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


def test_jd_driven_directions_remain_jd_required_and_not_routable(tmp_path):
    database_path = tmp_path / "career-map.sqlite"
    import_packs(database_path)

    with sqlite3.connect(database_path) as connection:
        rows = connection.execute(
            """SELECT external_key, knowledge_maturity, service_mode, runtime_status, requires_specific_jd
               FROM career_directions ORDER BY external_key"""
        ).fetchall()

    assert len(rows) == 6
    assert all(maturity == "research" for _, maturity, _, _, _ in rows)
    assert all(mode == "jd_driven" and status == "not_routable" and requires_jd == 1 for _, _, mode, status, requires_jd in rows)
