import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from medical_career_agent.adapters.json_career_repository import JsonCareerRepository
from medical_career_agent.adapters.json_profile_repository import (
    JsonMedicalProfileRepository,
)
from medical_career_agent.application.career_explorer import CareerExplorationAgent


class CareerComparisonTest(unittest.TestCase):
    def setUp(self):
        self.profiles = JsonMedicalProfileRepository(ROOT / "data" / "profiles")
        self.careers = JsonCareerRepository(ROOT / "data" / "careers")
        self.agent = CareerExplorationAgent(self.profiles, self.careers)

    def test_three_profiles_produce_expected_revisable_hypotheses(self):
        expectations = {
            "synthetic-clinical-communicator-001": {
                "first": "medical-science-liaison",
                "included": {
                    "medical-science-liaison",
                    "medical-writer",
                    "clinical-research-associate",
                },
            },
            "synthetic-research-builder-002": {
                "first": "healthcare-ai-product-manager",
                "included": {
                    "healthcare-ai-product-manager",
                    "medical-writer",
                },
            },
            "synthetic-safety-coordinator-003": {
                "first": "pharmacovigilance-specialist",
                "included": {
                    "pharmacovigilance-specialist",
                    "medical-writer",
                    "clinical-research-associate",
                },
            },
        }

        for profile_id, expected in expectations.items():
            with self.subTest(profile_id=profile_id):
                first = self.agent.compare_profile(profile_id=profile_id)
                second = self.agent.compare_profile(profile_id=profile_id)
                self.assertEqual(first, second)
                self.assertLessEqual(len(first.hypotheses), 3)
                self.assertEqual(first.hypotheses[0].career_id, expected["first"])
                actual_ids = {item.career_id for item in first.hypotheses}
                self.assertTrue(expected["included"].issubset(actual_ids))
                self.assertIn("rank_revisable_hypotheses", first.trace)

    def test_every_hypothesis_is_traceable_to_profile_and_career_sources(self):
        for profile in self.profiles.list():
            run = self.agent.compare_profile(profile_id=profile.profile_id)
            profile_evidence_ids = {item.evidence_id for item in profile.evidence}

            for hypothesis in run.hypotheses:
                career = self.careers.get(hypothesis.career_id)
                career_source_ids = {item.source_id for item in career.sources}
                support_ids = {
                    item.evidence_id for item in hypothesis.supporting_evidence
                }

                self.assertTrue(support_ids)
                self.assertFalse(support_ids - profile_evidence_ids)
                self.assertLessEqual(
                    hypothesis.evidence_coverage_percent,
                    hypothesis.raw_evidence_coverage_percent,
                )
                self.assertTrue(hypothesis.counter_evidence)
                self.assertTrue(hypothesis.unknowns)
                self.assertIn(hypothesis.validation_action, career.validation_actions)

                for component in hypothesis.components:
                    self.assertTrue(component.career_source_ids)
                    self.assertFalse(
                        set(component.career_source_ids) - career_source_ids
                    )
                for caution in hypothesis.counter_evidence:
                    self.assertFalse(set(caution.source_ids) - career_source_ids)

    def test_travel_non_negotiable_deprioritizes_uncertain_paths(self):
        research_run = self.agent.compare_profile(
            profile_id="synthetic-research-builder-002"
        )
        safety_run = self.agent.compare_profile(
            profile_id="synthetic-safety-coordinator-003"
        )

        research_findings = {
            item.career_id: item for item in research_run.constraint_findings
        }
        safety_findings = {
            item.career_id: item for item in safety_run.constraint_findings
        }
        self.assertEqual(
            research_findings["medical-science-liaison"].status,
            "needs_role_check",
        )
        self.assertEqual(
            safety_findings["clinical-research-associate"].status,
            "potential_conflict",
        )

        cra = next(
            item
            for item in safety_run.hypotheses
            if item.career_id == "clinical-research-associate"
        )
        self.assertLess(
            cra.evidence_coverage_percent,
            cra.raw_evidence_coverage_percent,
        )

    def test_invalid_limits_and_unknown_profiles_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "maximum_hypotheses"):
            self.agent.compare_profile(
                profile_id="synthetic-clinical-communicator-001",
                maximum_hypotheses=4,
            )
        with self.assertRaisesRegex(LookupError, "unknown profile_id"):
            self.agent.compare_profile(profile_id="missing-profile")


if __name__ == "__main__":
    unittest.main()
