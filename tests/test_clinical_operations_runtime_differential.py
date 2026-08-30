from pathlib import Path

from src.medical_career_agent.services.bullet_composer import BulletComposerService
from src.medical_career_agent.services.claim_gate import ClaimGateService


ROOT = Path(__file__).parents[1]
ROLE_PACKS = ROOT / "data" / "role-packs"


def _overlapping_clinical_fact_set():
    return {
        "schema_version": "canonical-experience-v2",
        "experience_id": "clinical_operations_overlap_1",
        "evidence_ids": ["ev_crf_1"],
        "context": {"domain": "clinical_research", "setting": "research_project", "topic": "study support"},
        "role": {"title": "research assistant", "responsibility_level": "participated"},
        "actions": ["crf_maintenance", "query_follow_up", "document_filing", "visit_scheduling"],
        "methods": ["data_quality_check", "document_control"],
        "tools": ["edc"],
        "techniques": [],
        "objects": ["crf", "investigator_file"],
        "collaboration": ["research_team"],
        "artifacts": ["investigator_file"],
        "outcomes": [],
        "scope": {},
        "unknowns": [],
        "activities": [{
            "activity_id": "activity_crf_1",
            "label": "confirmed CRF and document support",
            "components": {
                "actions": ["crf_maintenance", "query_follow_up", "document_filing", "visit_scheduling"],
                "methods": ["data_quality_check", "document_control"],
                "tools": ["edc"],
                "techniques": [],
                "objects": ["crf", "investigator_file"],
                "artifacts": ["investigator_file"],
            },
            "evidence_ids": ["ev_crf_1"],
            "status": "user_confirmed",
        }],
        "task_responsibilities": [{
            "responsibility_id": "responsibility_crf_1",
            "activity_id": "activity_crf_1",
            "ownership_level": "contributed",
            "execution_mode": "supervised",
            "scope": {"coverage": "partial", "note": "specified study-support steps"},
            "evidence_ids": ["ev_crf_1"],
        }],
        "status": "user_confirmed",
    }


def test_clinical_research_and_operations_preserve_the_same_confirmed_fact_set():
    canonical = _overlapping_clinical_fact_set()
    composer = BulletComposerService(role_packs_dir=ROLE_PACKS)
    gate = ClaimGateService(role_packs_dir=ROLE_PACKS)
    research = composer.compose_bullets(canonical_experience=canonical, role_pack_name="clinical_research_v1")[0].to_dict()
    operations = composer.compose_bullets(canonical_experience=canonical, role_pack_name="clinical_operations_v1")[0].to_dict()

    assert research["role_pack"] == "clinical_research_v1"
    assert operations["role_pack"] == "clinical_operations_v1"
    for field in ("used_facts", "dependency_refs", "evidence_ids", "project_responsibility_level"):
        assert operations[field] == research[field]
    assert gate.validate_claim(bullet_claim=research, canonical_experience=canonical).status == "ready"
    assert gate.validate_claim(bullet_claim=operations, canonical_experience=canonical).status == "ready"
    assert not any(phrase in operations["wording"] for phrase in ("trial ownership", "project ownership", "operations ownership", "临床运营负责人", "项目或项目群所有权", "流程或运营所有者"))
