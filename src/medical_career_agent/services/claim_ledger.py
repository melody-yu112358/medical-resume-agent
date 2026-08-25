from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from ..adapters.file_session_store import FileSessionStore


@dataclass(frozen=True)
class ClaimRecord:
    """A record of a bullet claim with full audit trail."""

    claim_id: str
    experience_id: str
    role_pack: str
    version: str
    evidence_ids: List[str]
    gate_status: str
    user_disposition: Optional[str]
    processed_at: str
    is_valid: bool = True
    invalidated_reason: Optional[str] = None
    dependency_refs: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "claim_id": self.claim_id,
            "experience_id": self.experience_id,
            "role_pack": self.role_pack,
            "version": self.version,
            "evidence_ids": self.evidence_ids,
            "gate_status": self.gate_status,
            "user_disposition": self.user_disposition,
            "processed_at": self.processed_at,
            "is_valid": self.is_valid,
        }
        if self.invalidated_reason:
            result["invalidated_reason"] = self.invalidated_reason
        if self.dependency_refs is not None:
            result["dependency_refs"] = self.dependency_refs
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClaimRecord":
        """Create from dictionary."""
        return cls(
            claim_id=data["claim_id"],
            experience_id=data["experience_id"],
            role_pack=data["role_pack"],
            version=data["version"],
            evidence_ids=data["evidence_ids"],
            gate_status=data["gate_status"],
            user_disposition=data.get("user_disposition"),
            processed_at=data["processed_at"],
            is_valid=data.get("is_valid", True),
            invalidated_reason=data.get("invalidated_reason"),
            dependency_refs=data.get("dependency_refs"),
        )


class ClaimLedgerService:
    """Manages the ledger of bullet claims with audit trail and validity tracking."""

    def __init__(self, sessions_path: Optional[Path] = None):
        """Initialize the claim ledger service.

        Args:
            sessions_path: Path to sessions directory. If None, uses default location.
        """
        if sessions_path is None:
            root = Path(__file__).parents[3]
            sessions_path = root / "data" / ".sessions"

        self.sessions_path = sessions_path
        self.sessions_path.mkdir(parents=True, exist_ok=True)
        self._next_claim_id = 1

    def _get_session_claims_file(self, session_id: str) -> Path:
        """Get the claims file path for a session."""
        return self.sessions_path / f"{session_id}.claims.json"

    def _load_session_claims(self, session_id: str) -> Dict[str, ClaimRecord]:
        """Load all claims for a session."""
        claims_file = self._get_session_claims_file(session_id)
        if not claims_file.exists():
            return {}

        try:
            data = json.loads(claims_file.read_text(encoding="utf-8"))
            return {claim_id: ClaimRecord.from_dict(claim_data)
                   for claim_id, claim_data in data.items()}
        except (json.JSONDecodeError, KeyError, TypeError):
            # Corrupted file, start fresh
            return {}

    def _save_session_claims(self, session_id: str, claims: Dict[str, ClaimRecord]) -> None:
        """Save all claims for a session."""
        claims_file = self._get_session_claims_file(session_id)
        data = {claim_id: claim.to_dict() for claim_id, claim in claims.items()}
        claims_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def record_claim(
        self,
        *,
        session_id: str,
        bullet_claim: Dict[str, Any],
        gate_status: str,
        user_disposition: Optional[str] = None,
    ) -> ClaimRecord:
        """Record a new bullet claim in the ledger.

        Args:
            session_id: The session identifier
            bullet_claim: The bullet claim data (must conform to bullet-claim.schema.json)
            gate_status: The verification status from the confirmation gate
            user_disposition: User's final decision (accepted, edited, rejected, or None)

        Returns:
            The recorded ClaimRecord
        """
        # Validate required fields from bullet claim
        required_fields = ["claim_id", "experience_id", "role_pack", "evidence_ids"]
        for field in required_fields:
            if field not in bullet_claim:
                raise ValueError(f"Missing required field in bullet_claim: {field}")

        # Create claim record
        claim_record = ClaimRecord(
            claim_id=bullet_claim["claim_id"],
            experience_id=bullet_claim["experience_id"],
            role_pack=bullet_claim["role_pack"],
            version=bullet_claim.get("schema_version", "bullet-claim-v1"),
            evidence_ids=bullet_claim["evidence_ids"],
            gate_status=gate_status,
            user_disposition=user_disposition,
            processed_at=datetime.now(timezone.utc).isoformat(),
            dependency_refs=bullet_claim.get("dependency_refs"),
        )

        # Load existing claims and add/update this one
        claims = self._load_session_claims(session_id)
        claims[claim_record.claim_id] = claim_record
        self._save_session_claims(session_id, claims)

        return claim_record

    def get_claim(self, session_id: str, claim_id: str) -> Optional[ClaimRecord]:
        """Get a specific claim by ID."""
        claims = self._load_session_claims(session_id)
        return claims.get(claim_id)

    def get_session_claims(self, session_id: str) -> List[ClaimRecord]:
        """Get all claims for a session."""
        claims = self._load_session_claims(session_id)
        return list(claims.values())

    def get_valid_claims_for_experience(self, session_id: str, experience_id: str) -> List[ClaimRecord]:
        """Get all valid claims for a specific experience."""
        claims = self._load_session_claims(session_id)
        return [
            claim for claim in claims.values()
            if claim.experience_id == experience_id and claim.is_valid
        ]

    def get_valid_claims_for_role_pack(self, session_id: str, role_pack: str) -> List[ClaimRecord]:
        """Get all valid claims for a specific role pack."""
        claims = self._load_session_claims(session_id)
        return [
            claim for claim in claims.values()
            if claim.role_pack == role_pack and claim.is_valid
        ]

    def invalidate_claims_by_experience(
        self,
        session_id: str,
        experience_id: str,
        reason: str = "experience_superseded",
    ) -> List[str]:
        """Invalidate all claims associated with an experience.

        Args:
            session_id: The session identifier
            experience_id: The experience ID to invalidate claims for
            reason: Reason for invalidation

        Returns:
            List of invalidated claim IDs
        """
        claims = self._load_session_claims(session_id)
        invalidated_ids = []

        for claim_id, claim in claims.items():
            if claim.experience_id == experience_id and claim.is_valid:
                # Create a new record with invalidation
                invalidated_claim = ClaimRecord(
                    claim_id=claim.claim_id,
                    experience_id=claim.experience_id,
                    role_pack=claim.role_pack,
                    version=claim.version,
                    evidence_ids=claim.evidence_ids,
                    gate_status=claim.gate_status,
                    user_disposition=claim.user_disposition,
                    processed_at=claim.processed_at,
                    is_valid=False,
                    invalidated_reason=reason,
                    dependency_refs=claim.dependency_refs,
                )
                claims[claim_id] = invalidated_claim
                invalidated_ids.append(claim_id)

        if invalidated_ids:
            self._save_session_claims(session_id, claims)

        return invalidated_ids

    def invalidate_claims_by_ids(
        self,
        session_id: str,
        claim_ids: List[str],
        reason: str = "user_rejected",
    ) -> List[str]:
        """Invalidate specific claims by their IDs.

        Args:
            session_id: The session identifier
            claim_ids: List of claim IDs to invalidate
            reason: Reason for invalidation

        Returns:
            List of successfully invalidated claim IDs
        """
        claims = self._load_session_claims(session_id)
        invalidated_ids = []

        for claim_id in claim_ids:
            if claim_id in claims and claims[claim_id].is_valid:
                claim = claims[claim_id]
                invalidated_claim = ClaimRecord(
                    claim_id=claim.claim_id,
                    experience_id=claim.experience_id,
                    role_pack=claim.role_pack,
                    version=claim.version,
                    evidence_ids=claim.evidence_ids,
                    gate_status=claim.gate_status,
                    user_disposition=claim.user_disposition,
                    processed_at=claim.processed_at,
                    is_valid=False,
                    invalidated_reason=reason,
                    dependency_refs=claim.dependency_refs,
                )
                claims[claim_id] = invalidated_claim
                invalidated_ids.append(claim_id)

        if invalidated_ids:
            self._save_session_claims(session_id, claims)

        return invalidated_ids

    def invalidate_claims_by_activity_dependencies(self, session_id: str, activity_ids: List[str], changed_fact_refs: List[str] | None = None, reason: str = "activity_changed") -> List[str]:
        """Selective invalidation; incomplete/legacy dependency records fail closed."""
        claims = self._load_session_claims(session_id)
        targets = set(activity_ids)
        fact_refs = set(changed_fact_refs or [])
        invalidated: List[str] = []
        for claim_id, claim in claims.items():
            if not claim.is_valid:
                continue
            deps = claim.dependency_refs or {}
            complete = deps.get("completeness") == "complete"
            linked = bool(targets.intersection(deps.get("activity_ids", [])))
            conservative = not complete and bool(fact_refs)
            if linked or conservative:
                claims[claim_id] = ClaimRecord(**{**claim.__dict__, "is_valid": False, "invalidated_reason": reason})
                invalidated.append(claim_id)
        if invalidated:
            self._save_session_claims(session_id, claims)
        return invalidated

    def get_invalidated_claims(self, session_id: str) -> List[ClaimRecord]:
        """Get all invalidated claims for a session."""
        claims = self._load_session_claims(session_id)
        return [claim for claim in claims.values() if not claim.is_valid]

    def cleanup_session_claims(self, session_id: str) -> None:
        """Remove all claims for a session (cleanup)."""
        claims_file = self._get_session_claims_file(session_id)
        if claims_file.exists():
            claims_file.unlink()
