from pathlib import Path

from src.medical_career_agent.services.bullet_composer import BulletComposerService
from src.medical_career_agent.services.claim_gate import ClaimGateService
from src.medical_career_agent.services.confirmation_gate import ConfirmationGateService
from src.medical_career_agent.services.claim_ledger import ClaimLedgerService


def _draft():
    return {"extracted_facts": {"context": {"domain": "clinical_research", "setting": "research_project", "topic": None}, "role": {"title": None, "responsibility_level": "participated"}, "actions": ["perform_analysis", "screen_studies"], "methods": ["sensitivity_analysis", "systematic_review"], "tools": ["r"], "techniques": [], "objects": ["research_data", "medical_literature"], "collaboration": [], "artifacts": [], "outcomes": [], "scope": {}, "unknown_items": []}}


def _activity(activity_id, action, method, tool, obj, evidence="ev_001"):
    return {"activity_id": activity_id, "label": "展示名称不能作为事实依据", "components": {"actions": [action], "methods": [method], "tools": [tool] if tool else [], "techniques": [], "objects": [obj], "artifacts": []}, "evidence_ids": [evidence], "status": "user_confirmed"}


def test_v2_confirmation_requires_all_activity_components_to_have_evidence_mapping():
    result = ConfirmationGateService().confirm_experience(
        experience_draft=_draft(),
        user_actions={"disposition": "accept", "canonical_schema_version": "canonical-experience-v2", "activities": [_activity("act_r", "perform_analysis", "sensitivity_analysis", "r", "research_data")], "task_responsibilities": [{"responsibility_id": "resp_r", "activity_id": "act_r", "ownership_level": "owned_component", "execution_mode": "independent", "scope": {"coverage": "partial", "note": "后续步骤"}, "evidence_ids": ["ev_001"]}]},
        evidence_records=[{"evidence_id": "ev_001", "source_text": "使用 R 完成敏感性分析", "status": "confirmed"}],
    )
    assert result.canonical_experience is not None
    assert result.canonical_experience["schema_version"] == "canonical-experience-v2"


def test_v2_reject_does_not_create_canonical_experience():
    result = ConfirmationGateService().confirm_experience(experience_draft=_draft(), user_actions={"disposition": "reject", "canonical_schema_version": "canonical-experience-v2"}, evidence_records=[{"evidence_id": "ev_001", "source_text": "x", "status": "confirmed"}])
    assert result.canonical_experience is None


def test_v2_rejects_two_current_responsibilities_for_one_activity():
    activity = _activity("act_r", "perform_analysis", "sensitivity_analysis", "r", "research_data")
    responsibilities = [
        {"responsibility_id": "resp_1", "activity_id": "act_r", "ownership_level": "contributed", "execution_mode": "supervised", "scope": {"coverage": "partial", "note": None}, "evidence_ids": ["ev_001"]},
        {"responsibility_id": "resp_2", "activity_id": "act_r", "ownership_level": "owned_component", "execution_mode": "independent", "scope": {"coverage": "partial", "note": None}, "evidence_ids": ["ev_001"]},
    ]
    result = ConfirmationGateService().confirm_experience(experience_draft=_draft(), user_actions={"disposition": "accept", "canonical_schema_version": "canonical-experience-v2", "activities": [activity], "task_responsibilities": responsibilities}, evidence_records=[{"evidence_id": "ev_001", "source_text": "使用 R 完成敏感性分析", "status": "confirmed"}])
    assert result.canonical_experience is None
    assert "only one current confirmed responsibility" in str(result.confirmation_status)


def test_composer_and_gate_use_activity_not_display_label():
    canonical = {"schema_version": "canonical-experience-v2", "experience_id": "exp_v2_1", "evidence_ids": ["ev_001"], "context": {"domain": "clinical_research", "setting": "research_project", "topic": None}, "role": {"title": None, "responsibility_level": "participated"}, "actions": ["screen_studies"], "methods": ["systematic_review"], "tools": [], "techniques": [], "objects": ["medical_literature"], "collaboration": [], "artifacts": [], "outcomes": [], "scope": {}, "unknowns": [], "activities": [_activity("act_screen", "screen_studies", "systematic_review", "", "medical_literature")], "task_responsibilities": [{"responsibility_id": "resp_screen", "activity_id": "act_screen", "ownership_level": "owned_component", "execution_mode": "independent", "scope": {"coverage": "full", "note": None}, "evidence_ids": ["ev_001"]}], "status": "user_confirmed"}
    composer = BulletComposerService(role_packs_dir=Path(__file__).parent.parent / "data" / "role-packs")
    claim = composer.compose_bullets(canonical_experience=canonical, role_pack_name="doctoral_v1")[0].to_dict()
    assert "展示名称" not in claim["wording"]
    assert "独立完成" in claim["wording"]
    assert ClaimGateService(role_packs_dir=Path(__file__).parent.parent / "data" / "role-packs").validate_claim(bullet_claim=claim, canonical_experience=canonical).status == "ready"


def test_v2_composer_renders_every_supported_component_without_internal_ids():
    activity = {
        "activity_id": "act_dense", "label": "已确认活动",
        "components": {
            "actions": ["perform_analysis"], "methods": ["meta_analysis"],
            "tools": ["stata"], "techniques": ["qpcr"], "objects": ["research_data"],
            "artifacts": ["analysis_figures"],
        },
        "evidence_ids": ["ev_001"], "status": "user_confirmed",
    }
    canonical = {
        "schema_version": "canonical-experience-v2", "experience_id": "exp_dense_labels",
        "evidence_ids": ["ev_001"], "context": {},
        "role": {"title": None, "responsibility_level": "participated"},
        "actions": ["perform_analysis"], "methods": ["meta_analysis"],
        "tools": ["stata"], "techniques": ["qpcr"], "objects": ["research_data"],
        "collaboration": [], "artifacts": ["analysis_figures"], "outcomes": [],
        "scope": {}, "unknowns": [], "activities": [activity],
        "task_responsibilities": [{
            "responsibility_id": "resp_dense", "activity_id": "act_dense",
            "ownership_level": "contributed", "execution_mode": "supervised",
            "scope": {"coverage": "partial", "note": "完成已分配步骤"},
            "evidence_ids": ["ev_001"],
        }],
        "status": "user_confirmed",
    }
    composer = BulletComposerService(
        role_packs_dir=Path(__file__).parent.parent / "data" / "role-packs"
    )
    claim = composer.compose_bullets(
        canonical_experience=canonical, role_pack_name="doctoral_v1"
    )[0].to_dict()

    assert all(
        label in claim["wording"]
        for label in ("统计分析", "Meta 分析", "Stata", "qPCR", "分析图表")
    )
    assert all(
        internal_id not in claim["wording"]
        for internal_id in ("perform_analysis", "meta_analysis", "stata", "qpcr", "analysis_figures")
    )
    assert ClaimGateService(
        role_packs_dir=Path(__file__).parent.parent / "data" / "role-packs"
    ).validate_claim(bullet_claim=claim, canonical_experience=canonical).status == "ready"


def test_v2_composer_uses_natural_activity_sentences_not_quoted_label_lists():
    composer = BulletComposerService(
        role_packs_dir=Path(__file__).parent.parent / "data" / "role-packs"
    )
    responsibility = {
        "ownership_level": "contributed", "execution_mode": "supervised",
        "scope": {"coverage": "full", "note": None},
    }

    retrieval = composer._render_v2_wording({
        "actions": ["retrieve_literature"], "methods": [],
        "tools": ["pubmed", "web_of_science"], "techniques": [],
        "artifacts": [],
    }, responsibility)
    analysis = composer._render_v2_wording({
        "actions": ["perform_analysis"], "methods": ["meta_analysis"],
        "tools": ["r"], "techniques": [], "artifacts": ["analysis_figures"],
    }, responsibility)

    assert retrieval == "在指导下参与医学文献检索，使用 PubMed、Web of Science。"
    assert analysis == "在指导下参与统计分析，采用 Meta 分析并使用 R，形成分析图表。"
    assert all(mark not in retrieval + analysis for mark in ("“", "”"))


def test_v2_partial_scope_is_worded_as_assigned_work_not_complete_ownership():
    wording = BulletComposerService._render_v2_wording({
        "actions": ["screen_studies"], "methods": [], "tools": [],
        "techniques": [], "artifacts": [],
    }, {
        "ownership_level": "contributed", "execution_mode": "supervised",
        "scope": {"coverage": "partial", "note": "完成已分配步骤"},
    })

    assert wording == "在指导下完成已分配的文献筛选。"
    assert "完整" not in wording


def test_v2_role_pack_priorities_change_order_without_changing_claim_set():
    activities = [
        {
            "activity_id": "act_retrieve", "label": "检索",
            "components": {
                "actions": ["retrieve_literature"], "methods": [],
                "tools": ["pubmed"], "techniques": [],
                "objects": ["medical_literature"], "artifacts": [],
            },
            "evidence_ids": ["ev_retrieve"], "status": "user_confirmed",
        },
        {
            "activity_id": "act_analysis", "label": "分析",
            "components": {
                "actions": ["perform_analysis"], "methods": ["meta_analysis"],
                "tools": ["r"], "techniques": [],
                "objects": ["research_data"], "artifacts": [],
            },
            "evidence_ids": ["ev_analysis"], "status": "user_confirmed",
        },
    ]
    responsibilities = [{
        "responsibility_id": f"resp_{name}", "activity_id": f"act_{name}",
        "ownership_level": "contributed", "execution_mode": "supervised",
        "scope": {"coverage": "full", "note": None},
        "evidence_ids": [f"ev_{name}"],
    } for name in ("retrieve", "analysis")]
    canonical = {
        "schema_version": "canonical-experience-v2", "experience_id": "exp_order",
        "evidence_ids": ["ev_retrieve", "ev_analysis"], "context": {},
        "role": {"title": None, "responsibility_level": "participated"},
        "actions": ["retrieve_literature", "perform_analysis"],
        "methods": ["meta_analysis"], "tools": ["pubmed", "r"],
        "techniques": [], "objects": ["medical_literature", "research_data"],
        "collaboration": [], "artifacts": [], "outcomes": [], "scope": {},
        "unknowns": [], "activities": activities,
        "task_responsibilities": responsibilities, "status": "user_confirmed",
    }
    composer = BulletComposerService(
        role_packs_dir=Path(__file__).parent.parent / "data" / "role-packs"
    )

    medical_affairs = composer.compose_bullets(
        canonical_experience=canonical, role_pack_name="medical_affairs_v1"
    )
    health_data = composer.compose_bullets(
        canonical_experience=canonical, role_pack_name="health_ai_data_v1"
    )

    assert medical_affairs[0].activity_id == "act_retrieve"
    assert health_data[0].activity_id == "act_analysis"
    assert {item.activity_id for item in medical_affairs} == {
        item.activity_id for item in health_data
    } == {"act_retrieve", "act_analysis"}


def test_v2_composer_keeps_every_distinct_confirmed_responsibility_auditable():
    specs = [
        ("retrieve", "retrieve_literature", "systematic_review", "pubmed", "medical_literature"),
        ("screen", "screen_studies", "systematic_review", "", "medical_literature"),
        ("extract", "extract_data", "systematic_review", "", "research_data"),
        ("meta", "perform_analysis", "meta_analysis", "revman", "research_data"),
        ("sensitivity", "perform_analysis", "sensitivity_analysis", "r", "research_data"),
    ]
    activities = [
        _activity(f"act_{name}", action, method, tool, obj, f"ev_{index:03d}")
        for index, (name, action, method, tool, obj) in enumerate(specs, 1)
    ]
    responsibilities = [{
        "responsibility_id": f"resp_{name}", "activity_id": f"act_{name}",
        "ownership_level": "contributed", "execution_mode": "supervised",
        "scope": {"coverage": "partial", "note": "完成已分配步骤"},
        "evidence_ids": [f"ev_{index:03d}"],
    } for index, (name, *_rest) in enumerate(specs, 1)]
    canonical = {
        "schema_version": "canonical-experience-v2", "experience_id": "exp_dense",
        "evidence_ids": [f"ev_{index:03d}" for index in range(1, 6)],
        "context": {"domain": "clinical_research", "setting": "research_project", "topic": "cardiovascular"},
        "role": {"title": None, "responsibility_level": "participated"},
        "actions": [item[1] for item in specs], "methods": [item[2] for item in specs],
        "tools": [item[3] for item in specs if item[3]], "techniques": [],
        "objects": [item[4] for item in specs], "collaboration": [],
        "artifacts": [], "outcomes": [], "scope": {}, "unknowns": [],
        "activities": activities, "task_responsibilities": responsibilities,
        "status": "user_confirmed",
    }
    composer = BulletComposerService(
        role_packs_dir=Path(__file__).parent.parent / "data" / "role-packs"
    )
    gate = ClaimGateService(
        role_packs_dir=Path(__file__).parent.parent / "data" / "role-packs"
    )

    claims = [
        item.to_dict() for item in composer.compose_bullets(
            canonical_experience=canonical, role_pack_name="doctoral_v1"
        )
    ]

    assert len(claims) == 5
    assert len({item["wording"] for item in claims}) == 5
    assert {
        item["dependency_refs"]["activity_ids"][0] for item in claims
    } == {item["activity_id"] for item in activities}
    assert all(
        gate.validate_claim(
            bullet_claim=claim, canonical_experience=canonical
        ).status == "ready"
        for claim in claims
    )


def test_v2_gate_rejects_partial_activity_rendered_as_full():
    canonical = {"schema_version": "canonical-experience-v2", "experience_id": "exp_v2_2", "evidence_ids": ["ev_001"], "context": {}, "role": {"responsibility_level": "participated"}, "actions": ["perform_analysis"], "methods": ["sensitivity_analysis"], "tools": ["r"], "techniques": [], "objects": ["research_data"], "collaboration": [], "artifacts": [], "outcomes": [], "scope": {}, "unknowns": [], "activities": [_activity("act_r", "perform_analysis", "sensitivity_analysis", "r", "research_data")], "task_responsibilities": [{"responsibility_id": "resp_r", "activity_id": "act_r", "ownership_level": "owned_component", "execution_mode": "independent", "scope": {"coverage": "partial", "note": None}, "evidence_ids": ["ev_001"]}], "status": "user_confirmed"}
    claim = {"schema_version": "bullet-claim-v2", "claim_id": "claim_v2_2", "experience_id": "exp_v2_2", "role_pack": "doctoral_v1", "wording": "独立完成 R 完整流程。", "used_facts": ["actions:perform_analysis", "methods:sensitivity_analysis", "tools:r"], "dependency_refs": {"activity_ids": ["act_r"], "responsibility_ids": ["resp_r"], "completeness": "complete"}, "evidence_ids": ["ev_001"], "project_responsibility_level": "participated", "omitted_unknowns": [], "risk_flags": [], "verification_status": "candidate", "user_disposition": None}
    result = ClaimGateService(role_packs_dir=Path(__file__).parent.parent / "data" / "role-packs").validate_claim(bullet_claim=claim, canonical_experience=canonical)
    assert result.status == "needs_confirmation"
    assert "scope_not_upgraded" in str(result.failed_checks)


def test_ledger_invalidates_incomplete_dependency_claim_conservatively(tmp_path):
    ledger = ClaimLedgerService(tmp_path)
    ledger.record_claim(session_id="s1", bullet_claim={"claim_id": "claim_1", "experience_id": "exp_1", "role_pack": "doctoral_v1", "evidence_ids": ["ev_001"]}, gate_status="ready")
    assert ledger.invalidate_claims_by_activity_dependencies("s1", ["act_x"], ["actions:screen_studies"])
