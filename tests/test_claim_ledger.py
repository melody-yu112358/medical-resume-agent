import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from src.medical_career_agent.services.claim_ledger import (
    ClaimLedgerService,
    ClaimRecord,
)


@pytest.fixture
def temp_sessions_path(tmp_path):
    """Create a temporary sessions directory for testing."""
    sessions_path = tmp_path / "sessions"
    sessions_path.mkdir()
    return sessions_path


@pytest.fixture
def claim_ledger(temp_sessions_path):
    """Create a claim ledger service instance for testing."""
    return ClaimLedgerService(sessions_path=temp_sessions_path)


@pytest.fixture
def sample_bullet_claim():
    """Provide a sample bullet claim for testing."""
    return {
        "schema_version": "bullet-claim-v1",
        "claim_id": "claim_001",
        "experience_id": "exp_abc123",
        "role_pack": "clinical_research_v1",
        "wording": "Conducted clinical research studies on patient outcomes",
        "used_facts": ["context.domain", "role.responsibility_level"],
        "evidence_ids": ["ev_001"],
        "responsibility_level": "owned_component",
        "omitted_unknowns": [],
        "risk_flags": [],
        "verification_status": "ready",
        "user_disposition": "accepted",
    }


def test_record_claim(claim_ledger, sample_bullet_claim):
    """Test recording a new claim."""
    session_id = "test_session_1"

    # Record the claim
    claim_record = claim_ledger.record_claim(
        session_id=session_id,
        bullet_claim=sample_bullet_claim,
        gate_status="verified",
        user_disposition="accepted",
    )

    # Verify the recorded claim
    assert claim_record.claim_id == "claim_001"
    assert claim_record.experience_id == "exp_abc123"
    assert claim_record.role_pack == "clinical_research_v1"
    assert claim_record.version == "bullet-claim-v1"
    assert claim_record.evidence_ids == ["ev_001"]
    assert claim_record.gate_status == "verified"
    assert claim_record.user_disposition == "accepted"
    assert claim_record.is_valid is True
    assert claim_record.processed_at is not None

    # Verify it can be retrieved
    retrieved = claim_ledger.get_claim(session_id, "claim_001")
    assert retrieved == claim_record


def test_get_session_claims(claim_ledger, sample_bullet_claim):
    """Test getting all claims for a session."""
    session_id = "test_session_2"

    # Record multiple claims
    claim1 = claim_ledger.record_claim(
        session_id=session_id,
        bullet_claim={**sample_bullet_claim, "claim_id": "claim_001"},
        gate_status="verified",
        user_disposition="accepted",
    )

    claim2 = claim_ledger.record_claim(
        session_id=session_id,
        bullet_claim={**sample_bullet_claim, "claim_id": "claim_002", "role_pack": "doctoral_v1"},
        gate_status="needs_review",
        user_disposition=None,
    )

    # Get all claims
    claims = claim_ledger.get_session_claims(session_id)
    assert len(claims) == 2
    assert claim1 in claims
    assert claim2 in claims


def test_get_valid_claims_for_experience(claim_ledger, sample_bullet_claim):
    """Test getting valid claims for a specific experience."""
    session_id = "test_session_3"

    # Record claims for different experiences
    claim_ledger.record_claim(
        session_id=session_id,
        bullet_claim={**sample_bullet_claim, "claim_id": "claim_001"},
        gate_status="verified",
        user_disposition="accepted",
    )

    claim_ledger.record_claim(
        session_id=session_id,
        bullet_claim={**sample_bullet_claim, "claim_id": "claim_002", "experience_id": "exp_def456"},
        gate_status="verified",
        user_disposition="accepted",
    )

    # Get claims for specific experience
    claims = claim_ledger.get_valid_claims_for_experience(session_id, "exp_abc123")
    assert len(claims) == 1
    assert claims[0].claim_id == "claim_001"


def test_get_valid_claims_for_role_pack(claim_ledger, sample_bullet_claim):
    """Test getting valid claims for a specific role pack."""
    session_id = "test_session_4"

    # Record claims for different role packs
    claim_ledger.record_claim(
        session_id=session_id,
        bullet_claim={**sample_bullet_claim, "claim_id": "claim_001"},
        gate_status="verified",
        user_disposition="accepted",
    )

    claim_ledger.record_claim(
        session_id=session_id,
        bullet_claim={**sample_bullet_claim, "claim_id": "claim_002", "role_pack": "doctoral_v1"},
        gate_status="verified",
        user_disposition="accepted",
    )

    # Get claims for specific role pack
    claims = claim_ledger.get_valid_claims_for_role_pack(session_id, "clinical_research_v1")
    assert len(claims) == 1
    assert claims[0].claim_id == "claim_001"


def test_invalidate_claims_by_experience(claim_ledger, sample_bullet_claim):
    """Test invalidating claims by experience ID."""
    session_id = "test_session_5"

    # Record multiple claims for the same experience
    claim_ledger.record_claim(
        session_id=session_id,
        bullet_claim={**sample_bullet_claim, "claim_id": "claim_001"},
        gate_status="verified",
        user_disposition="accepted",
    )

    claim_ledger.record_claim(
        session_id=session_id,
        bullet_claim={**sample_bullet_claim, "claim_id": "claim_002"},
        gate_status="verified",
        user_disposition="accepted",
    )

    # Invalidate claims for the experience
    invalidated_ids = claim_ledger.invalidate_claims_by_experience(
        session_id=session_id,
        experience_id="exp_abc123",
        reason="experience_superseded",
    )

    assert len(invalidated_ids) == 2
    assert "claim_001" in invalidated_ids
    assert "claim_002" in invalidated_ids

    # Verify claims are now invalid
    claim1 = claim_ledger.get_claim(session_id, "claim_001")
    assert claim1 is not None
    assert claim1.is_valid is False
    assert claim1.invalidated_reason == "experience_superseded"

    # Verify valid claims query returns empty
    valid_claims = claim_ledger.get_valid_claims_for_experience(session_id, "exp_abc123")
    assert len(valid_claims) == 0


def test_invalidate_specific_claims(claim_ledger, sample_bullet_claim):
    """Test invalidating specific claims by ID."""
    session_id = "test_session_6"

    # Record multiple claims
    claim_ledger.record_claim(
        session_id=session_id,
        bullet_claim={**sample_bullet_claim, "claim_id": "claim_001"},
        gate_status="verified",
        user_disposition="accepted",
    )

    claim_ledger.record_claim(
        session_id=session_id,
        bullet_claim={**sample_bullet_claim, "claim_id": "claim_002"},
        gate_status="verified",
        user_disposition="accepted",
    )

    # Invalidate specific claims
    invalidated_ids = claim_ledger.invalidate_claims_by_ids(
        session_id=session_id,
        claim_ids=["claim_001"],
        reason="user_rejected",
    )

    assert len(invalidated_ids) == 1
    assert invalidated_ids[0] == "claim_001"

    # Verify claim_001 is invalid but claim_002 is still valid
    claim1 = claim_ledger.get_claim(session_id, "claim_001")
    assert claim1 is not None
    assert claim1.is_valid is False

    claim2 = claim_ledger.get_claim(session_id, "claim_002")
    assert claim2 is not None
    assert claim2.is_valid is True


def test_get_invalidated_claims(claim_ledger, sample_bullet_claim):
    """Test getting all invalidated claims."""
    session_id = "test_session_7"

    # Record and invalidate some claims
    claim_ledger.record_claim(
        session_id=session_id,
        bullet_claim={**sample_bullet_claim, "claim_id": "claim_001"},
        gate_status="verified",
        user_disposition="accepted",
    )

    claim_ledger.record_claim(
        session_id=session_id,
        bullet_claim={**sample_bullet_claim, "claim_id": "claim_002"},
        gate_status="verified",
        user_disposition="accepted",
    )

    claim_ledger.invalidate_claims_by_ids(
        session_id=session_id,
        claim_ids=["claim_001"],
        reason="user_rejected",
    )

    # Get invalidated claims
    invalidated_claims = claim_ledger.get_invalidated_claims(session_id)
    assert len(invalidated_claims) == 1
    assert invalidated_claims[0].claim_id == "claim_001"
    assert invalidated_claims[0].is_valid is False


def test_claim_record_serialization():
    """Test ClaimRecord serialization and deserialization."""
    original = ClaimRecord(
        claim_id="claim_123",
        experience_id="exp_456",
        role_pack="medical_affairs_v1",
        version="bullet-claim-v1",
        evidence_ids=["ev_001", "ev_002"],
        gate_status="verified",
        user_disposition="accepted",
        processed_at="2026-08-22T10:00:00Z",
        is_valid=True,
        invalidated_reason=None,
    )

    # Serialize to dict
    data = original.to_dict()

    # Deserialize back to ClaimRecord
    restored = ClaimRecord.from_dict(data)

    assert restored == original


def test_missing_required_fields_in_bullet_claim(claim_ledger):
    """Test that missing required fields raise ValueError."""
    session_id = "test_session_8"

    # Test missing claim_id
    with pytest.raises(ValueError, match="Missing required field in bullet_claim: claim_id"):
        claim_ledger.record_claim(
            session_id=session_id,
            bullet_claim={"experience_id": "exp_123", "role_pack": "test", "evidence_ids": ["ev_1"]},
            gate_status="verified",
        )

    # Test missing experience_id
    with pytest.raises(ValueError, match="Missing required field in bullet_claim: experience_id"):
        claim_ledger.record_claim(
            session_id=session_id,
            bullet_claim={"claim_id": "claim_123", "role_pack": "test", "evidence_ids": ["ev_1"]},
            gate_status="verified",
        )


def test_cleanup_session_claims(claim_ledger, sample_bullet_claim):
    """Test cleaning up all claims for a session."""
    session_id = "test_session_9"

    # Record some claims
    claim_ledger.record_claim(
        session_id=session_id,
        bullet_claim=sample_bullet_claim,
        gate_status="verified",
        user_disposition="accepted",
    )

    # Verify claims exist
    claims = claim_ledger.get_session_claims(session_id)
    assert len(claims) == 1

    # Cleanup
    claim_ledger.cleanup_session_claims(session_id)

    # Verify no claims remain
    claims = claim_ledger.get_session_claims(session_id)
    assert len(claims) == 0