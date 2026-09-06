"""Taxonomy applicability, facet semantics, and incremental artifact regressions."""
import json

import pytest

from test_career_map_revisions import source_tree, build, read_json, write_json, manifest, rows
from test_career_map_viewer import viewer
from medical_career_agent.career_map_viewer import create_viewer, matches_filters


def test_same_dimension_or_cross_dimension_and():
    entry = {"ecosystems": [{"code": "academic"}], "lifecycle_stages": [{"code": "clinical"}]}
    assert matches_filters(entry, {"ecosystems": ["academic", "pharma"], "lifecycle_stages": []})
    assert not matches_filters(entry, {"ecosystems": ["academic"], "lifecycle_stages": ["postmarketing"]})
    assert matches_filters(entry, {"ecosystems": ["academic"], "lifecycle_stages": ["postmarketing"]}, exclude="lifecycle_stages")


def test_academic_stage_counts_and_empty_result_recovery(viewer):
    client, _ = viewer
    html = client.get("/", query_string={"ecosystems": "academic_research"}).get_data(as_text=True)
    assert "当前显示 2 个方向" in html
    assert "生命周期已标注 1 个，待确认 1 个，不适用 0 个" in html
    assert "Clinical Development（1）" in html
    assert "Post-marketing Safety（0）" in html
    assert "生命周期 · 可选阶段：待确认" in html
    html = client.get("/", query_string={"ecosystems": "academic_research", "lifecycle_stages": "post_marketing_safety"}).get_data(as_text=True)
    assert "当前显示 0 个方向" in html
    assert "当前知识库没有同时标注这些条件的方向" in html
    assert 'href="/?ecosystems=academic_research"' in html
    assert "生命周期已标注 1 个，待确认 1 个" in html


def test_multiple_values_preserved_and_unknown_value_rejected(viewer):
    client, _ = viewer
    args = [("ecosystems", "academic_research"), ("ecosystems", "cro_smo"), ("lifecycle_stages", "clinical_development")]
    html = client.get("/", query_string=args).get_data(as_text=True)
    assert "当前显示 4 个方向" in html
    assert 'value="academic_research" checked' in html and 'value="cro_smo" checked' in html
    assert 'href="/?ecosystems=academic_research&amp;ecosystems=cro_smo"' in html
    # Count for the facet itself ignores both selected ecosystem codes.
    assert "Pharma / Biotech（1）" in html
    assert client.get("/", query_string=args + [("ecosystems", "unknown")]).status_code == 400


@pytest.mark.parametrize("state,stages,review", [
    ("unknown", [], None), ("mapped", [], None), ("pending", ["clinical_development"], None),
    ("not_applicable", [], None), ("not_applicable", [], {"reviewed_by": "test", "reviewed_at": "bad-date", "reason": "fixture"}),
])
def test_invalid_applicability_does_not_activate_snapshot(source_tree, tmp_path, state, stages, review):
    db = tmp_path / "map.sqlite"
    build(source_tree, db)
    before = manifest(db)
    path = source_tree / "data/career-map/directions-v1.json"
    registry = read_json(path)
    assignment = registry["canonical_role_pack_taxonomy"][0]
    assignment.update(lifecycle_applicability=state, lifecycle_stages=stages)
    if review is not None:
        assignment["lifecycle_review"] = review
    write_json(path, registry)
    with pytest.raises(ValueError):
        build(source_tree, db)
    assert manifest(db) == before


def test_applicability_uses_imported_revision_fresh_incremental_and_history(source_tree, tmp_path):
    incremental, fresh = tmp_path / "incremental.sqlite", tmp_path / "fresh.sqlite"
    build(source_tree, incremental)
    old = manifest(incremental)
    path = source_tree / "data/career-map/directions-v1.json"
    registry = read_json(path)
    assignment = registry["canonical_role_pack_taxonomy"][0]
    assignment["lifecycle_applicability"] = "not_applicable"
    assignment["lifecycle_review"] = {"reviewed_by": "synthetic test reviewer", "reviewed_at": "2026-09-06", "reason": "Synthetic applicability transition fixture; not a domain assertion."}
    write_json(path, registry)
    # Unimported source edits must not leak into the UI.
    client = create_viewer(incremental).test_client()
    url = "/?role=doctoral_v1"
    assert "生命周期：待确认" in client.get(url).get_data(as_text=True)
    build(source_tree, incremental)
    build(source_tree, fresh)
    assert manifest(incremental) == manifest(fresh)
    assert "不适用（已审核）" in client.get(url).get_data(as_text=True)
    assert "synthetic test reviewer" in client.get(url).get_data(as_text=True)
    old_registry = json.loads(rows(incremental, "SELECT raw_content FROM source_artifacts WHERE artifact_id=?", (old["taxonomy_revision"],))[0][0])
    assert old_registry["canonical_role_pack_taxonomy"][0]["lifecycle_applicability"] == "pending"
    # Removing metadata restores legacy pending semantics without stale status.
    assignment.pop("lifecycle_applicability")
    assignment.pop("lifecycle_review")
    write_json(path, registry)
    build(source_tree, incremental)
    build(source_tree, fresh)
    assert manifest(incremental) == manifest(fresh)
    assert "生命周期：待确认" in client.get(url).get_data(as_text=True)
