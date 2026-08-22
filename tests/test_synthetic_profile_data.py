import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
PROFILE_DIR = ROOT / "data" / "profiles"
CAREER_DIR = ROOT / "data" / "careers"
EVALUATION_FILE = (
    ROOT / "data" / "evaluations" / "synthetic-profile-cases.cn.json"
)
PROFILE_SCHEMA_FILE = ROOT / "schemas" / "medical_profile.schema.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class SyntheticProfileDataTest(unittest.TestCase):
    def setUp(self):
        self.profiles = [load_json(path) for path in sorted(PROFILE_DIR.glob("*.json"))]
        self.evaluation = load_json(EVALUATION_FILE)
        self.career_ids = {
            load_json(path)["career_id"] for path in CAREER_DIR.glob("*.json")
        }

    def test_profiles_are_explicitly_synthetic_and_traceable(self):
        schema = load_json(PROFILE_SCHEMA_FILE)
        required_fields = set(schema["required"])

        self.assertEqual(len(self.profiles), 3)
        for profile in self.profiles:
            self.assertFalse(required_fields - set(profile))
            self.assertEqual(profile["profile_type"], "synthetic")
            self.assertFalse(profile["consent_recorded"])
            self.assertIn("虚构", profile["scenario_note"])
            self.assertTrue(profile["evidence"])

            evidence_ids = [item["evidence_id"] for item in profile["evidence"]]
            self.assertEqual(len(evidence_ids), len(set(evidence_ids)))
            for item in profile["evidence"]:
                self.assertTrue(item["statement"].strip())
                self.assertTrue(item["capabilities"])
                self.assertEqual(item["source_reference"], "synthetic scenario")

    def test_evaluation_cases_reference_existing_profiles_evidence_and_careers(self):
        profiles_by_id = {profile["profile_id"]: profile for profile in self.profiles}
        cases_by_id = {case["profile_id"]: case for case in self.evaluation["cases"]}

        self.assertEqual(set(profiles_by_id), set(cases_by_id))
        for profile_id, case in cases_by_id.items():
            evidence_ids = {
                item["evidence_id"] for item in profiles_by_id[profile_id]["evidence"]
            }
            hypotheses = case["expected_hypotheses"]

            self.assertGreaterEqual(len(hypotheses), 1)
            self.assertLessEqual(len(hypotheses), 3)
            self.assertTrue(case["constraint_checks"])
            self.assertTrue(case["forbidden_conclusions"])

            for hypothesis in hypotheses:
                self.assertIn(hypothesis["career_id"], self.career_ids)
                self.assertTrue(hypothesis["supporting_evidence_ids"])
                self.assertFalse(
                    set(hypothesis["supporting_evidence_ids"]) - evidence_ids
                )
                self.assertTrue(hypothesis["counter_evidence"])
                self.assertTrue(hypothesis["unknowns"])
                self.assertTrue(hypothesis["validation_action"].strip())


if __name__ == "__main__":
    unittest.main()
