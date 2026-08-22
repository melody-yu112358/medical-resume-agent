import pytest
from src.medical_career_agent.services.confirmation_gate import ConfirmationGateService


def test_confirm_experience_missing_evidence_records():
    """Test confirmation with missing evidence records."""
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
        "disposition": "accept",
        "confirmed_facts": ["all"]
    }

    # Empty evidence records
    evidence_records = []

    result = service.confirm_experience(
        experience_draft=experience_draft,
        user_actions=user_actions,
        evidence_records=evidence_records
    )

    assert result.confirmation_status["status"] == "needs_more_info"
    assert "evidence_records" in str(result.confirmation_status["missing_confirmations"])
    assert result.canonical_experience is None


def test_confirm_experience_responsibility_upgrade_without_evidence():
    """Test upgrading responsibility level without providing new evidence."""
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
        "disposition": "edit",
        "confirmed_facts": ["all"],
        "modified_facts": {
            "role.responsibility_level": "owned_component"
        },
        "new_evidence": ""  # No new evidence provided
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

    assert result.confirmation_status["status"] == "needs_more_info"
    assert "responsibility_level_evidence" in str(result.confirmation_status["missing_confirmations"])
    assert result.canonical_experience is None


def test_confirm_experience_missing_required_fields():
    """Test that missing required fields cause validation failure."""
    service = ConfirmationGateService()

    # This test simulates missing critical fields like context or role
    experience_draft = {
        "extracted_facts": {
            # Missing context entirely
            # Missing role entirely
            "actions": ["retrieve_literature"],
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
        evidence_records=evidence_records
    )

    # Should fail validation due to missing required fields
    assert result.confirmation_status["status"] == "needs_more_info"
    assert result.canonical_experience is None
    assert len(result.confirmation_status["validation_errors"]) > 0
    assert any("Missing required category" in error for error in result.confirmation_status["validation_errors"])
    assert len(result.confirmation_status["validation_errors"]) > 0


def test_confirm_experience_participated_is_valid_final_level():
    """Test that 'participated' is a valid final responsibility level."""
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
            "source_text": "参与系统综述的文献检索和筛选工作",
            "status": "confirmed"
        }
    ]

    result = service.confirm_experience(
        experience_draft=experience_draft,
        user_actions=user_actions,
        evidence_records=evidence_records
    )

    # participated should be accepted as a valid final level
    assert result.confirmation_status["status"] == "ready"
    assert result.canonical_experience is not None
    assert result.canonical_experience["role"]["responsibility_level"] == "participated"
    assert result.canonical_experience["status"] == "user_confirmed"


def test_confirm_experience_no_auto_upgrade_from_keywords():
    """Test that system doesn't auto-upgrade responsibility based on keywords."""
    service = ConfirmationGateService()

    # Experience draft should have conservative "participated" level even if
    # original text contained words like "负责"
    experience_draft = {
        "extracted_facts": {
            "context": {"domain": "clinical_research", "setting": "research_project", "topic": None},
            "role": {"title": None, "responsibility_level": "participated"},  # Conservative default
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
        "risk_flags": ["可能存在责任等级升级风险"]
    }

    user_actions = {
        "disposition": "accept",
        "confirmed_facts": ["all"]
    }

    evidence_records = [
        {
            "evidence_id": "ev_001",
            "source_text": "负责系统综述的文献检索工作",
            "status": "confirmed"
        }
    ]

    result = service.confirm_experience(
        experience_draft=experience_draft,
        user_actions=user_actions,
        evidence_records=evidence_records
    )

    # Should keep "participated" since user didn't explicitly upgrade it
    assert result.confirmation_status["status"] == "ready"
    assert result.canonical_experience is not None
    assert result.canonical_experience["role"]["responsibility_level"] == "participated"