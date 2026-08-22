from __future__ import annotations

from ..domain.career_models import CareerComparisonRun, MedicalProfile
from ..ports.repositories import CareerRepository, MedicalProfileRepository
from ..services.career_comparator import CareerComparator, SCORING_VERSION


class CareerExplorationAgent:
    """Structured profile -> sourced, revisable career hypotheses."""

    def __init__(
        self,
        profiles: MedicalProfileRepository,
        careers: CareerRepository,
        comparator: CareerComparator | None = None,
    ) -> None:
        self.profiles = profiles
        self.careers = careers
        self.comparator = comparator or CareerComparator()

    def compare_profile(
        self, *, profile_id: str, maximum_hypotheses: int = 3
    ) -> CareerComparisonRun:
        trace = ["retrieve_profile"]
        profile = self.profiles.get(profile_id)
        return self.compare_profile_record(
            profile=profile,
            maximum_hypotheses=maximum_hypotheses,
            initial_trace=trace,
        )

    def compare_profile_record(
        self,
        *,
        profile: MedicalProfile,
        maximum_hypotheses: int = 3,
        initial_trace: list[str] | None = None,
    ) -> CareerComparisonRun:
        trace = list(initial_trace or ["receive_confirmed_profile"])
        trace.append("retrieve_career_cards")
        careers = self.careers.list()
        trace.append("apply_constraints_and_compare_evidence")
        hypotheses, findings = self.comparator.compare(
            profile,
            careers,
            maximum_hypotheses=maximum_hypotheses,
        )
        trace.append("rank_revisable_hypotheses")
        return CareerComparisonRun(
            profile_id=profile.profile_id,
            considered_career_ids=tuple(career.career_id for career in careers),
            hypotheses=hypotheses,
            constraint_findings=findings,
            trace=tuple(trace),
            scoring_version=SCORING_VERSION,
        )
