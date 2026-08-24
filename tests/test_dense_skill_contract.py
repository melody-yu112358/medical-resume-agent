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
