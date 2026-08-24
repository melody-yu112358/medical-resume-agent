from pathlib import Path


ROOT = Path(__file__).parents[1]
SKILL = ROOT / "skill-lite" / "medical-resume-skill"


def test_dense_skill_declares_three_tiers_and_evidence_scaled_density():
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")

    assert "Conservative" in text
    assert "Professional (default)" in text
    assert "High impact" in text
    assert "5–9" in text
    assert "3–6" in text
    assert "dense-resume-protocol.md" in text


def test_dense_protocol_requires_distinct_supported_dimensions():
    text = (SKILL / "references" / "dense-resume-protocol.md").read_text(encoding="utf-8")

    assert "Omit unsupported dimensions" in text
    assert "Two bullets are duplicates" in text
    assert "one fact set" in text
    assert "hard-coded candidate information" in text


def test_html_asset_supports_complete_medical_resume_sections():
    text = (SKILL / "assets" / "ats-medical-resume.html").read_text(encoding="utf-8")

    for heading in ("个人概况", "教育背景", "科研经历", "项目与实践经历", "临床经历", "成果与学术输出", "方法与技能"):
        assert heading in text
    for placeholder in ("{{research_bullets_html}}", "{{project_bullets_html}}", "{{clinical_bullets_html}}"):
        assert placeholder in text
    assert "{{optional_photo_html}}" in text
    assert ".profile-photo" in text


def test_html_delivery_keeps_photo_opt_in_and_local():
    text = (SKILL / "references" / "html-delivery.md").read_text(encoding="utf-8")

    assert "Do not use a photo by default" in text
    assert "relative path" in text
    assert "must not be uploaded" in text


def test_codex_agent_metadata_is_present():
    text = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")

    assert 'display_name: "Medical Resume Skill"' in text
    assert "$medical-resume-skill" in text


def test_prompt_contracts_keep_generation_staged_and_fact_bound():
    text = (SKILL / "references" / "prompt-templates.md").read_text(encoding="utf-8")

    for stage in ("Stage 1", "Stage 2", "Stage 3", "Stage 4", "Stage 5"):
        assert stage in text
    assert "Stop after this stage until the user confirms" in text
    assert "fact set" in text
    assert '"status": "ready|revision_required"' in text
    assert "candidate-information source" in text


def test_skill_has_non_skippable_sample_and_reaudit_gates():
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")

    assert "Mandatory workflow gates" in text
    assert "representative sample" in text
    assert "project-level role" in text
    assert "task-level responsibility" in text
    assert "user-edited" in text
    assert "Tier selection" in (SKILL / "references" / "prompt-templates.md").read_text(encoding="utf-8")


def test_editor_is_offline_editable_and_supports_three_themes():
    text = (SKILL / "assets" / "resume-editor.html").read_text(encoding="utf-8")

    for feature in ("localStorage", "导入 Markdown", "下载 Markdown", "导出独立 HTML", "打印 / PDF"):
        assert feature in text
    for theme in ("clinical-blue", "academic-green", "ats-mono"):
        assert theme in text
    assert "<script src=" not in text
    assert "https://" not in text


def test_delivery_contract_requires_complete_tiers_and_data_driven_files():
    text = (SKILL / "references" / "resume-data-contract.md").read_text(encoding="utf-8")

    for tier in ("conservative", "professional", "high_impact"):
        assert tier in text
    for output in ("resume.md", "resume.html", "resume-editor.html"):
        assert output in text
    assert "complete candidate-facing resume" in text
    assert "never type candidate facts directly" in text


def test_pdf_export_has_explicit_fallbacks_and_no_false_success():
    text = (SKILL / "scripts" / "export_resume_pdf.py").read_text(encoding="utf-8")

    assert "export_with_playwright" in text
    assert "export_with_edge" in text
    assert "return 2" in text
    assert "do not report a PDF as delivered" in text
