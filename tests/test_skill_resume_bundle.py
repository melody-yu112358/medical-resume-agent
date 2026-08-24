from __future__ import annotations

import importlib.util
import json
import shutil
import uuid
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skill-lite" / "medical-resume-skill"
SCRIPT = SKILL / "scripts" / "build_resume_bundle.py"


def _module():
    spec = importlib.util.spec_from_file_location("build_resume_bundle", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _data() -> dict:
    base = "# 张同学\n> 医学科研申请 · user@example.com\n\n## 科研经历\n### Meta 分析课题\n- 参与文献筛选并使用 R 完成已确认的统计分析。"
    return {
        "schema_version": "medical-resume-data-v1",
        "candidate": {"name": "张同学", "target_direction": "医学科研申请", "contact": "user@example.com", "photo": None},
        "fact_card": {"responsibility": "participated"},
        "tiers": {
            "conservative": {"markdown": base + "\n- 稳妥版完整正文。"},
            "professional": {"markdown": base + "\n- 专业版完整正文。"},
            "high_impact": {"markdown": base + "\n- 高密度版完整正文。"},
        },
        "selected_tier": "professional",
        "theme": "academic-green",
        "edit_status": "generated",
        "audit": {"status": "ready"},
    }


def _test_root() -> Path:
    root = ROOT / ".test-artifacts" / f"resume-bundle-{uuid.uuid4().hex}"
    root.mkdir(parents=True)
    return root


def test_bundle_is_generated_from_selected_tier():
    module = _module()
    test_root = _test_root()
    try:
        source = test_root / "resume-data.json"
        source.write_text(json.dumps(_data(), ensure_ascii=False), encoding="utf-8")
        output = test_root / "resume-output"
        created = module.build_bundle(source, output, SKILL)

        assert {path.name for path in created} == {"resume-data.json", "resume.md", "resume.html", "resume-editor.html"}
        assert "专业版完整正文" in (output / "resume.md").read_text(encoding="utf-8")
        assert "专业版完整正文" in (output / "resume.html").read_text(encoding="utf-8")
        editor = (output / "resume-editor.html").read_text(encoding="utf-8")
        assert "专业版完整正文" in editor
        assert "__INITIAL_MARKDOWN_JSON__" not in editor
        assert "__THEME__" not in editor
    finally:
        shutil.rmtree(test_root, ignore_errors=True)


def test_bundle_rejects_missing_complete_tier():
    module = _module()
    data = _data()
    data["tiers"]["high_impact"]["markdown"] = ""
    test_root = _test_root()
    try:
        source = test_root / "resume-data.json"
        source.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

        with pytest.raises(ValueError, match="high_impact"):
            module.build_bundle(source, test_root / "output", SKILL)
    finally:
        shutil.rmtree(test_root, ignore_errors=True)


def test_markdown_renderer_escapes_candidate_html():
    module = _module()
    rendered = module.markdown_to_html("# 姓名\n- <script>alert(1)</script> **已确认**")

    assert "<script>" not in rendered
    assert "&lt;script&gt;" in rendered
    assert "<strong>已确认</strong>" in rendered
