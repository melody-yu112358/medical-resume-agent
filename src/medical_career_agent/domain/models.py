from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any


@dataclass(frozen=True)
class SourceRef:
    url: str
    collected_at: date
    label: str = "public_job_posting"


@dataclass(frozen=True)
class SalaryEvidence:
    minimum: int | None
    maximum: int | None
    months_per_year: int | None = None
    currency: str = "CNY"
    period: str = "month"
    raw_text: str = ""


@dataclass(frozen=True)
class JobPosting:
    job_id: str
    title: str
    company: str
    location: str
    description: str
    requirements: tuple[str, ...]
    salary: SalaryEvidence
    source: SourceRef
    synthetic: bool = False
    employment_type: str | None = None
    experience: str | None = None
    education: str | None = None
    salary_raw: str | None = None
    verification_status: str = "unknown"
    career_name: str = "未知方向"
    source_quality: str | None = None
    responsibilities: tuple[str, ...] = ()
    raw_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ResumeEvidence:
    statement: str
    skill: str
    source: str = "resume"


@dataclass(frozen=True)
class ResumeProfile:
    raw_text: str
    skills: tuple[str, ...]
    evidence: tuple[ResumeEvidence, ...]
    unknowns: tuple[str, ...] = ()


@dataclass(frozen=True)
class MatchReport:
    job_id: str
    score: int
    matched_requirements: tuple[str, ...]
    missing_requirements: tuple[str, ...]
    weighted_score: int | None = None
    max_weight: int = 0
    criterion_scores: tuple[dict[str, Any], ...] = ()
    supporting_evidence: tuple[ResumeEvidence, ...] = ()
    cautions: tuple[str, ...] = ()
    next_actions: tuple[str, ...] = ()
    scoring_version: str = "deterministic-v1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CareerRun:
    profile: ResumeProfile
    job: JobPosting
    report: MatchReport
    trace: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
