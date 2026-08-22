import pytest
from src.medical_career_agent.services.confirmation_gate import ConfirmationGateService


def test_confirm_experience_basic_accept():
    """Test basic acceptance of an experience draft."""
    service = ConfirmationGateService()

    # Mock experience draft from Action 3
    experience_draft = {
        "extracted_facts": {
            "context": {"domain": "clinical_research", "setting": "research_project", "topic": None},
            "role": {"title": None, "responsibility_level": "participated"},
            "actions": ["retrieve_literature", "screen_studies"],
            "methods": ["systematic_review"],
            "tools": ["spss"],
            "objects": ["medical_literature"],
            "collaboration": ["research_team"],
            "artifacts": ["prisma_flowchart"],
            "outcomes": [],
            "scope": {},
            "unknown_items": ["database_count", "study_count"]
        },
        "unknown_items": ["database_count", "study_count"],
        "possible_value_angles": ["文献检索能力在MSL岗位中非常重要"],
        "clarifying_questions": ["使用了哪些数据库进行文献检索？"],
        "risk_flags": []
    }

    user_actions = {
        "disposition": "accept",
        "confirmed_facts": ["all"]
    }

    evidence_records = [
        {
            "evidence_id": "ev_001",
            "source_text": "参与系统综述的文献检索和筛选工作",
            "status": "confirmed"
        }
    ]

    result = service.confirm_experience(
        experience_draft=experience_draft,
        user_actions=user_actions,
        evidence_records=evidence_records
    )

    assert result.confirmation_status["status"] == "ready"
    assert result.canonical_experience is not None
    assert result.canonical_experience["status"] == "user_confirmed"
    assert "ev_001" in result.canonical_experience["evidence_ids"]
    assert result.canonical_experience["role"]["responsibility_level"] == "participated"
    assert len(result.fact_evidence_map) > 0


def test_confirm_experience_with_modifications():
    """Test confirmation with user modifications and new evidence."""
    service = ConfirmationGateService()

    experience_draft = {
        "extracted_facts": {
            "context": {"domain": "clinical_research", "setting": "research_project", "topic": None},
            "role": {"title": None, "responsibility_level": "participated"},
            "actions": ["retrieve_literature"],
            "methods": ["systematic_review"],
            "tools": [],
            "objects": ["medical_literature"],
            "collaboration": [],
            "artifacts": [],
            "outcomes": [],
            "scope": {},
            "unknown_items": ["database_count"]
        },
        "unknown_items": ["database_count"],
        "possible_value_angles": [],
        "clarifying_questions": [],
        "risk_flags": []
    }

    user_actions = {
        "disposition": "edit",
        "confirmed_facts": ["all"],
        "modified_facts": {
            "tools": ["spss", "r"],
            "role.responsibility_level": "owned_component"
        },
        "new_evidence": "我负责使用SPSS和R进行数据分析，并主导了整个系统综述项目"
    }

    evidence_records = [
        {
            "evidence_id": "ev_001",
            "source_text": "参与系统综述工作",
            "status": "confirmed"
        }
    ]

    result = service.confirm_experience(
        experience_draft=experience_draft,
        user_actions=user_actions,
        evidence_records=evidence_records
    )

    assert result.confirmation_status["status"] == "edited"
    assert result.canonical_experience is not None
    assert result.canonical_experience["status"] == "user_confirmed"
    assert len(result.canonical_experience["evidence_ids"]) == 2  # Original + new
    assert "spss" in result.canonical_experience["tools"]
    assert "r" in result.canonical_experience["tools"]
    assert result.canonical_experience["role"]["responsibility_level"] == "owned_component"
    assert len(result.fact_evidence_map) > 0


def test_confirm_experience_rejection():
    """Test rejection of an experience draft."""
    service = ConfirmationGateService()

    experience_draft = {
        "extracted_facts": {
            "context": {"domain": "clinical_research", "setting": "research_project", "topic": None},
            "role": {"title": None, "responsibility_level": "participated"},
            "actions": ["retrieve_literature"],
            "methods": ["systematic_review"],
            "tools": [],
            "objects": ["medical_literature"],
            "collaboration": [],
            "artifacts": [],
            "outcomes": [],
            "scope": {},
            "unknown_items": []
        },
        "unknown_items": [],
        "possible_value_angles": [],
        "clarifying_questions": [],
        "risk_flags": []
    }

    user_actions = {
        "disposition": "reject"
    }

    evidence_records = [
        {
            "evidence_id": "ev_001",
            "source_text": "参与系统综述工作",
            "status": "confirmed"
        }
    ]

    result = service.confirm_experience(
        experience_draft=experience_draft,
        user_actions=user_actions,
        evidence_records=evidence_records
    )

    assert result.confirmation_status["status"] == "rejected"
    assert result.canonical_experience is not None
    assert result.canonical_experience["status"] == "rejected"
    assert "ev_001" in result.canonical_experience["evidence_ids"]
    assert result.fact_evidence_map == {}


def test_confirm_experience_with_previous_experience_id():
    """Test confirmation with a previous experience ID for invalidation."""
    service = ConfirmationGateService()

    experience_draft = {
        "extracted_facts": {
            "context": {"domain": "clinical_research", "setting": "research_project", "topic": None},
            "role": {"title": None, "responsibility_level": "participated"},
            "actions": ["retrieve_literature"],
            "methods": ["systematic_review"],
            "tools": ["spss"],
            "objects": ["medical_literature"],
            "collaboration": ["research_team"],
            "artifacts": ["prisma_flowchart"],
            "outcomes": [],
            "scope": {},
            "unknown_items": []
        },
        "unknown_items": [],
        "possible_value_angles": [],
        "clarifying_questions": [],
        "risk_flags": []
    }

    user_actions = {
        "disposition": "accept",
        "confirmed_facts": ["all"]
    }

    evidence_records = [
        {
            "evidence_id": "ev_001",
            "source_text": "参与系统综述工作",
            "status": "confirmed"
        }
    ]

    result = service.confirm_experience(
        experience_draft=experience_draft,
        user_actions=user_actions,
        evidence_records=evidence_records,
        previous_experience_id="exp_old123"
    )

    # Should create invalidation event for any fact change with previous experience ID
    assert result.confirmation_status["status"] == "ready"
    assert result.canonical_experience is not None
    assert result.canonical_experience["status"] == "user_confirmed"
    assert result.invalidation is not None
    assert result.invalidation["previous_experience_id"] == "exp_old123"
    assert result.invalidation["reason"] == "confirmed_fact_changed"
    assert result.invalidation["invalidate_related_claims"] is True


def test_rejection_with_previous_experience_id():
    """Test rejection with a previous experience ID creates invalidation."""
    service = ConfirmationGateService()

    experience_draft = {
        "extracted_facts": {
            "context": {"domain": "clinical_research", "setting": "research_project", "topic": None},
            "role": {"title": None, "responsibility_level": "participated"},
            "actions": ["retrieve_literature"],
            "methods": ["systematic_review"],
            "tools": [],
            "objects": ["medical_literature"],
            "collaboration": [],
            "artifacts": [],
            "outcomes": [],
            "scope": {},
            "unknown_items": []
        },
        "unknown_items": [],
        "possible_value_angles": [],
        "clarifying_questions": [],
        "risk_flags": []
    }

    user_actions = {
        "disposition": "reject"
    }

    evidence_records = [
        {
            "evidence_id": "ev_001",
            "source_text": "参与系统综述工作",
            "status": "confirmed"
        }
    ]

    result = service.confirm_experience(
        experience_draft=experience_draft,
        user_actions=user_actions,
        evidence_records=evidence_records,
        previous_experience_id="exp_old123"
    )

    assert result.confirmation_status["status"] == "rejected"
    assert result.invalidation is not None
    assert result.invalidation["previous_experience_id"] == "exp_old123"
    assert result.invalidation["reason"] == "user_rejected"
    assert result.invalidation["invalidate_related_claims"] is True