import sys
import unittest
from pathlib import Path
from jsonschema import validate, ValidationError

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

CANONICAL_SCHEMA_PATH = ROOT / "schemas" / "canonical-experience.schema.json"
ROLE_PACK_SCHEMA_PATH = ROOT / "schemas" / "role-pack.schema.json"
BULLET_CLAIM_SCHEMA_PATH = ROOT / "schemas" / "bullet-claim.schema.json"

class SchemaContractTest(unittest.TestCase):

    def test_canonical_experience_schema_accepts_valid_example(self):
        from json import loads
        schema = loads(CANONICAL_SCHEMA_PATH.read_text(encoding="utf-8"))
        example = loads((ROOT / "data" / "fixtures" / "canonical-experience-example.json").read_text(encoding="utf-8"))
        validate(instance=example, schema=schema)

    def test_canonical_experience_rejects_missing_required_fields(self):
        from json import loads
        schema = loads(CANONICAL_SCHEMA_PATH.read_text(encoding="utf-8"))
        invalid_example = {
            "schema_version": "canonical-experience-v1",
            "experience_id": "exp-test-001"
            # missing many required fields
        }
        with self.assertRaises(ValidationError):
            validate(instance=invalid_example, schema=schema)

    def test_canonical_experience_rejects_invalid_responsibility_level(self):
        from json import loads
        schema = loads(CANONICAL_SCHEMA_PATH.read_text(encoding="utf-8"))
        invalid_example = {
            "schema_version": "canonical-experience-v1",
            "experience_id": "exp-test-001",
            "evidence_ids": ["ev-001"],
            "context": {"domain": "clinical_research", "setting": "research_project"},
            "role": {"responsibility_level": "invalid_level"},  # invalid enum
            "actions": [],
            "methods": [],
            "tools": [],
            "objects": [],
            "collaboration": [],
            "artifacts": [],
            "outcomes": [],
            "scope": {},
            "unknowns": [],
            "status": "user_confirmed"
        }
        with self.assertRaises(ValidationError):
            validate(instance=invalid_example, schema=schema)

    def test_role_pack_schema_accepts_valid_config(self):
        from json import loads
        schema = loads(ROLE_PACK_SCHEMA_PATH.read_text(encoding="utf-8"))
        config = loads((ROOT / "data" / "role-packs" / "doctoral_v1.json").read_text(encoding="utf-8"))
        validate(instance=config, schema=schema)

    def test_bullet_claim_schema_accepts_valid_claim(self):
        from json import loads
        schema = loads(BULLET_CLAIM_SCHEMA_PATH.read_text(encoding="utf-8"))
        valid_claim = {
            "schema_version": "bullet-claim-v1",
            "claim_id": "claim_001",
            "experience_id": "exp_001",
            "role_pack": "doctoral_v1",
            "wording": "参与Meta分析的文献检索和筛选工作",
            "used_facts": ["retrieve_literature", "screen_studies"],
            "evidence_ids": ["ev_001"],
            "responsibility_level": "participated",
            "omitted_unknowns": ["study_count", "publication_status"],
            "risk_flags": [],
            "verification_status": "candidate",
            "user_disposition": None
        }
        validate(instance=valid_claim, schema=schema)

    def test_bullet_claim_rejects_invalid_verification_status(self):
        from json import loads
        schema = loads(BULLET_CLAIM_SCHEMA_PATH.read_text(encoding="utf-8"))
        invalid_claim = {
            "schema_version": "bullet-claim-v1",
            "claim_id": "claim-001",
            "experience_id": "exp-meta-001",
            "role_pack": "doctoral_v1",
            "wording": "参与Meta分析的文献检索和筛选工作",
            "used_facts": ["retrieve_literature", "screen_studies"],
            "evidence_ids": ["ev-001"],
            "responsibility_level": "participated",
            "omitted_unknowns": ["study_count", "publication_status"],
            "risk_flags": [],
            "verification_status": "invalid_status",  # invalid enum
            "user_disposition": None
        }
        with self.assertRaises(ValidationError):
            validate(instance=invalid_claim, schema=schema)


if __name__ == "__main__":
    unittest.main()