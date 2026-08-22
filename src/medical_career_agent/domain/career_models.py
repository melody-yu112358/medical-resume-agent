from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class MarketClaim:
    claim: str
    source_ids: tuple[str, ...]
    claim_type: str
    confidence: float | None = None


@dataclass(frozen=True)
class CareerSource:
    source_id: str
    title: str
    url: str
    publisher: str
    accessed_at: str


@dataclass(frozen=True)
class CareerRecord:
    career_id: str
    name: str
    market: str
    summary: str | None
    required_skills: tuple[MarketClaim, ...]
    medical_transferable_skills: tuple[MarketClaim, ...]
    work_environment: tuple[MarketClaim, ...]
    entry_barriers: tuple[MarketClaim, ...]
    validation_actions: tuple[str, ...]
    sources: tuple[CareerSource, ...]
    review_status: str


@dataclass(frozen=True)
class ProfileEvidence:
    evidence_id: str
    statement: str
    capabilities: tuple[str, ...]
    confidence: float | None = None


@dataclass(frozen=True)
class ProfileConstraints:
    locations: tuple[str, ...]
    weekly_learning_hours: float | None
    non_negotiables: tuple[str, ...]


@dataclass(frozen=True)
class MedicalProfile:
    profile_id: str
    profile_type: str
    education_field: str
    education_stage: str
    evidence: tuple[ProfileEvidence, ...]
    constraints: ProfileConstraints
    unknowns: tuple[str, ...]


@dataclass(frozen=True)
class CapabilityCoverage:
    group_id: str
    label: str
    weight: int
    matched: bool
    evidence_ids: tuple[str, ...]
    career_source_ids: tuple[str, ...]


@dataclass(frozen=True)
class SupportingEvidence:
    evidence_id: str
    statement: str
    capability_groups: tuple[str, ...]


@dataclass(frozen=True)
class ConstraintFinding:
    career_id: str
    constraint: str
    status: str
    explanation: str
    penalty_points: int
    career_source_ids: tuple[str, ...]


@dataclass(frozen=True)
class CareerHypothesis:
    career_id: str
    career_name: str
    rank: int
    evidence_coverage_percent: int
    raw_evidence_coverage_percent: int
    scoring_version: str
    components: tuple[CapabilityCoverage, ...]
    supporting_evidence: tuple[SupportingEvidence, ...]
    counter_evidence: tuple[MarketClaim, ...]
    gaps: tuple[str, ...]
    unknowns: tuple[str, ...]
    constraint_findings: tuple[ConstraintFinding, ...]
    validation_action: str
    career_review_status: str


@dataclass(frozen=True)
class CareerComparisonRun:
    profile_id: str
    considered_career_ids: tuple[str, ...]
    hypotheses: tuple[CareerHypothesis, ...]
    constraint_findings: tuple[ConstraintFinding, ...]
    trace: tuple[str, ...]
    scoring_version: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
