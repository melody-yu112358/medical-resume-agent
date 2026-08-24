from medical_career_agent.medical_resume_agent_v1 import MedicalResumeAgentV1


def test_raw_input_stops_for_confirmation_without_golden_fact_injection():
    agent = MedicalResumeAgentV1()

    result = agent.process_user_input("参加过组会，也做过Meta分析")

    assert result["status"] == "needs_confirmation"
    assert 1 <= len(result["clarifying_questions"]) <= 3
    serialized = str(result)
    for unconfirmed_value in ("45", "SPSS", "第三作者", "PRISMA流程图", "心血管临床研究背景"):
        assert unconfirmed_value not in serialized


def test_canonical_factory_does_not_fill_missing_business_facts():
    agent = MedicalResumeAgentV1()

    canonical = agent._create_canonical_experience(
        {
            "context": {"domain": "clinical_research", "setting": "research_project"},
            "role": {"responsibility_level": "participated"},
            "methods": ["meta_analysis"],
        }
    )

    assert canonical["methods"] == ["meta_analysis"]
    assert canonical["actions"] == []
    assert canonical["tools"] == []
    assert canonical["outcomes"] == []
    assert canonical["scope"] == {}
