from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ProfileEvidenceDraft:
    evidence_id: str
    source_quote: str
    capabilities: tuple[str, ...]
    confidence: float | None
    confirmation_status: str = "unverified"


@dataclass(frozen=True)
class MedicalProfileDraft:
    profile_id: str
    education_field: str
    education_stage: str
    evidence: tuple[ProfileEvidenceDraft, ...]
    locations: tuple[str, ...]
    weekly_learning_hours: float | None
    non_negotiables: tuple[str, ...]
    unknowns: tuple[str, ...]
    follow_up_question: str | None
    consent_recorded: bool
    persisted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
