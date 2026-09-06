"""Read-only local explorer integration and boundary tests."""
import hashlib
import sqlite3

import pytest

from test_career_map_revisions import source_tree, build
from medical_career_agent.career_map_viewer import create_viewer, read_database

CDM = "clinical_data_management_v1"
PROFILE = "synthetic-cdm-support-001"


@pytest.fixture()
def viewer(source_tree, tmp_path):
    db = tmp_path / "map.sqlite"
    build(source_tree, db)
    return create_viewer(db).test_client(), db


def test_catalog_cards_filters_and_unconfigured_directions(viewer):
    client, db = viewer
    html = client.get("/").get_data(as_text=True)
    assert "产业生态" in html and "16</strong>" in html and "5</strong>" in html
    assert "可试用解释" in html and "JD-driven 探索" in html
    with read_database(db) as conn:
        code = conn.execute("SELECT code FROM ecosystems LIMIT 1").fetchone()[0]
        roles = conn.execute("SELECT external_key FROM role_pack_versions WHERE is_current=1").fetchall()
    response = client.get("/", query_string={"ecosystems": code})
    assert response.status_code == 200
    with read_database(db) as conn:
        expected = conn.execute("SELECT COUNT(*) FROM role_ecosystems r JOIN ecosystems e USING(ecosystem_id) WHERE e.code=?", (code,)).fetchone()[0]
        expected += conn.execute("SELECT COUNT(*) FROM career_direction_ecosystems r JOIN ecosystems e USING(ecosystem_id) WHERE e.code=?", (code,)).fetchone()[0]
    assert f"当前显示 {expected} 个方向" in response.get_data(as_text=True)
    for role in roles:
        response = client.get("/", query_string={"role": role[0]})
        assert response.status_code == 200
    html = client.get("/", query_string={"role": "pharmacovigilance_drug_safety_v1"}).get_data(as_text=True)
    assert "尚未配置解释规则" in html


@pytest.mark.parametrize("role,profile", [(CDM, PROFILE), (CDM, "synthetic-cdm-quantitative-003"),
    ("medical_device_clinical_application_specialist_v1", "synthetic-device-application-002")])
def test_explanations_evidence_provenance_without_writes(viewer, role, profile):
    client, db = viewer
    before = hashlib.sha256(db.read_bytes()).hexdigest()
    response = client.get("/", query_string={"role": role, "profile": profile})
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "需要具体 JD" in html and "证据与条件" in html
    assert "背景研究来源，不是该 claim" in html
    assert "match_rule_revision" in html and "input_digest" in html
    if role == CDM:
        assert "摘要不一致" in html
    assert "禁止推断边界" in html
    assert response.headers["Cache-Control"] == "no-store"
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
    assert before == hashlib.sha256(db.read_bytes()).hexdigest()
    if profile == PROFILE:
        assert html.count('内部契约：') == 6  # no duplicate items for overlapping labels


@pytest.mark.parametrize("args,code", [({"role": "unknown"}, 404),
    ({"profile": "real-user", "role": CDM}, 400), ({"profile": PROFILE}, 400),
    ({"profile": PROFILE, "role": "pharmacovigilance_drug_safety_v1"}, 400),
    ({"profile_json": '{"statement":"private"}'}, 400), ({"ecosystems": "unknown"}, 400)])
def test_rejects_invalid_input(viewer, args, code):
    assert viewer[0].get("/", query_string=args).status_code == code


def test_loopback_and_method_boundaries(viewer):
    client, _ = viewer
    assert client.post("/", json={"profile": "private"}).status_code == 405
    assert client.get("/", environ_overrides={"REMOTE_ADDR": "192.168.1.2"}).status_code == 403
    assert client.get("/", headers={"Host": "external.example"}).status_code == 403
    assert client.get("/", query_string=[("role", CDM), ("role", CDM)]).status_code == 400
    assert client.get("/api/career-comparisons").status_code == 404
    response = client.get("/assets/career-map-filters.js")
    assert response.status_code == 200 and b"requestSubmit" in response.data
    assert "script-src 'self'" in response.headers["Content-Security-Policy"]
    assert client.get("/assets/other.js").status_code == 404


def test_missing_and_old_database_fail_without_creating_or_migrating(tmp_path):
    db = tmp_path / "missing.sqlite"
    with pytest.raises(ValueError, match="知识库不存在"):
        create_viewer(db)
    assert not db.exists()
    with sqlite3.connect(db) as conn:
        conn.execute("PRAGMA user_version=3")
    with pytest.raises(ValueError, match="版本不兼容"):
        create_viewer(db)
    with sqlite3.connect(db) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 3


def test_readonly_connection_blocks_writes(viewer):
    with read_database(viewer[1]) as conn:
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("DELETE FROM knowledge_snapshots")


def test_incompatible_interpreter_has_actionable_error(viewer, monkeypatch):
    from medical_career_agent.services.career_card_explanation import CareerCardExplanationService
    def fail(*args, **kwargs):
        raise ValueError("internal details should not leak")
    monkeypatch.setattr(CareerCardExplanationService, "explain", fail)
    response = viewer[0].get("/", query_string={"role": CDM, "profile": PROFILE})
    assert response.status_code == 503
    assert "重新运行导入脚本" in response.get_data(as_text=True)
    assert b"internal details" not in response.data


def test_query_pins_snapshot_and_escapes_rendered_evidence(viewer, monkeypatch):
    from medical_career_agent.services.career_card_explanation import CareerCardExplanationService
    original = CareerCardExplanationService.explain
    captured = []
    def explain(self, **kwargs):
        captured.append(kwargs["knowledge_snapshot_id"])
        result = original(self, **kwargs)
        result["items"][0]["explanation"] = '<script>alert("test")</script>'
        return result
    monkeypatch.setattr(CareerCardExplanationService, "explain", explain)
    html = viewer[0].get("/", query_string={"role": CDM, "profile": PROFILE}).get_data(as_text=True)
    assert len(captured) == 1 and captured[0].startswith("knowledge-")
    assert captured[0] in html
    assert '<script>' not in html and '&lt;script&gt;' in html
