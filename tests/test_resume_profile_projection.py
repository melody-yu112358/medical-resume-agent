from medical_career_agent.services.resume_profile_projection import project_confirmed_profile


def _activity(activity_id, methods, tools, evidence_ids, status="user_confirmed"):
    return {
        "activity_id": activity_id,
        "status": status,
        "components": {"methods": methods, "tools": tools},
        "evidence_ids": evidence_ids,
    }


def _canonical(experience_id, activities, evidence_ids, status="user_confirmed"):
    return {
        "schema_version": "canonical-experience-v2",
        "experience_id": experience_id,
        "status": status,
        "evidence_ids": evidence_ids,
        # Root values are extraction leftovers in v2 and must not be projected.
        "methods": ["mendelian_randomization"],
        "tools": ["stata"],
        "activities": activities,
    }


def test_v2_projection_uses_only_confirmed_activity_facts_and_their_evidence():
    projection = project_confirmed_profile([
        _canonical("exp_a", [
            _activity("act_a", ["systematic_review", "meta_analysis"], ["pubmed", "r"], ["ev_1"]),
            _activity("draft", ["case_control"], ["stata"], ["ev_1"], status="proposed"),
        ], ["ev_1"]),
        _canonical("exp_b", [
            _activity("act_b", ["meta_analysis", "sensitivity_analysis", "unknown_method"], ["r", "excel", "unknown_tool"], ["ev_2", "forged"]),
        ], ["ev_2"]),
        _canonical("unconfirmed", [
            _activity("act_c", ["cohort_study"], ["spss"], ["ev_3"]),
        ], ["ev_3"], status="model_draft"),
    ])

    by_name = {item["name"]: item for item in projection["skills"]}
    assert projection["summary"] == "基于已确认经历，积累了系统综述、Meta 分析与敏感性分析相关实践。"
    assert by_name["系统综述"] == {"name": "系统综述", "category": "research", "level": None, "evidence_ids": ["ev_1"]}
    assert by_name["Meta 分析"]["evidence_ids"] == ["ev_1", "ev_2"]
    assert by_name["R"]["evidence_ids"] == ["ev_1", "ev_2"]
    assert by_name["PubMed"]["category"] == "medical_information"
    assert by_name["Excel"]["category"] == "data"
    assert "孟德尔随机化（MR）" not in by_name
    assert "Stata" not in by_name
    assert "病例对照研究" not in by_name
    assert "unknown_method" not in str(projection)
    assert "unknown_tool" not in str(projection)
    assert "forged" not in projection["summary_evidence_ids"]
    assert projection["summary_evidence_ids"] == ["ev_1", "ev_2"]
    assert all(item["level"] is None for item in projection["skills"])


def test_legacy_confirmed_canonical_remains_supported_without_inferred_level():
    projection = project_confirmed_profile([{
        "schema_version": "canonical-experience-v1",
        "status": "user_confirmed",
        "evidence_ids": ["ev_legacy"],
        "methods": ["cohort_study"],
        "tools": ["spss"],
    }])

    assert projection["summary"] == "基于已确认经历，积累了队列研究与SPSS相关实践。"
    assert projection["skills"] == [
        {"name": "队列研究", "category": "research", "level": None, "evidence_ids": ["ev_legacy"]},
        {"name": "SPSS", "category": "data", "level": None, "evidence_ids": ["ev_legacy"]},
    ]


def test_tools_without_confirmed_methods_do_not_create_positioning_copy():
    projection = project_confirmed_profile([_canonical(
        "exp_tools", [_activity("act_tools", [], ["python"], ["ev_tools"])], ["ev_tools"]
    )])

    assert projection["summary"] is None
    assert projection["summary_evidence_ids"] == []
    assert projection["skills"] == [
        {"name": "Python", "category": "data", "level": None, "evidence_ids": ["ev_tools"]}
    ]


def test_one_confirmed_method_is_not_enough_for_candidate_positioning():
    projection = project_confirmed_profile([_canonical(
        "exp_method", [_activity("act_method", ["systematic_review"], [], ["ev_method"])], ["ev_method"]
    )])

    assert projection["summary"] is None
    assert projection["summary_evidence_ids"] == []
    assert projection["skills"][0]["name"] == "系统综述"
