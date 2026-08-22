import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCHEMA_PATH = ROOT / "schemas" / "resume_document.schema.json"
SAMPLE_PATH = ROOT / "tests" / "fixtures" / "resume_document.sample.json"


class ResumeSchemaContractTest(unittest.TestCase):
    def setUp(self):
        self.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.sample = json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))

    def test_medical_resume_schema_has_traceability_and_medical_sections(self):
        properties = self.schema["properties"]
        self.assertEqual(properties["schema_version"]["const"], "resume-document-v1")
        self.assertIn("clinical_experience", properties)
        self.assertIn("research_experience", properties)
        self.assertIn("publications", properties)
        self.assertIn("capability_profile", properties)
        self.assertIn("review_events", properties)
        self.assertEqual(
            properties["target"]["$ref"], "#/$defs/target"
        )

    def test_sample_references_existing_evidence_only(self):
        evidence_ids = {item["evidence_id"] for item in self.sample["evidence"]}
        self.assertEqual(len(evidence_ids), len(self.sample["evidence"]))
        self.assertEqual(self.sample["schema_version"], "resume-document-v1")
        for section in ("education", "clinical_experience", "professional_experience", "research_experience", "projects", "publications", "awards", "skills", "languages"):
            for item in self.sample.get(section, []):
                self.assertTrue(set(item["evidence_ids"]).issubset(evidence_ids))
                for bullet in item.get("bullets", []):
                    self.assertTrue(set(bullet["evidence_ids"]).issubset(evidence_ids))


if __name__ == "__main__":
    unittest.main()
