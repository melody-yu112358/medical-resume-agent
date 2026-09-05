import json
import sys
from pathlib import Path

import pytest
from jsonschema import validate


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from import_role_packs_to_career_map import import_packs  # noqa: E402
from medical_career_agent.services.career_card_explanation import (  # noqa: E402
    CareerCardExplanationService,
    EXPLANATION_CLASSES,
)


PROFILE_SET_PATH = ROOT / "data" / "career-map" / "career-card-explanation-test-profiles-v1.json"
PROFILE_SCHEMA_PATH = ROOT / "schemas" / "career-card-explanation-profile.schema.json"


@pytest.fixture()
def explanation_service(tmp_path):
    database_path = tmp_path / "career-map.sqlite"
    import_packs(database_path)
    return CareerCardExplanationService(database_path)


def _profiles_by_id():
    profile_set = json.loads(PROFILE_SET_PATH.read_text(encoding="utf-8"))
    schema = json.loads(PROFILE_SCHEMA_PATH.read_text(encoding="utf-8"))
    profiles = {profile["profile_id"]: profile for profile in profile_set["profiles"]}
    assert len(profiles) == 3
    for profile in profiles.values():
        validate(instance=profile, schema=schema)
    return profiles


def test_explanation_profiles_are_synthetic_and_schema_valid():
    profiles = _profiles_by_id()
    assert all(profile["profile_type"] == "synthetic" for profile in profiles.values())
    assert all("虚构" in profile["scenario_note"] for profile in profiles.values())


def test_cdm_explanation_uses_all_five_classes_and_traceable_provenance(explanation_service):
    profile = _profiles_by_id()["synthetic-cdm-support-001"]
    result = explanation_service.explain(profile=profile, role_pack="clinical_data_management_v1")

    assert tuple(result["explanations"]) == EXPLANATION_CLASSES
    assert {key: len(value) for key, value in result["explanations"].items()} == {
        "direct": 1,
        "transferable": 3,
        "partial": 2,
        "gap": 0,
        "unsupported": 1,
    }
    assert "evidence_coverage_percent" not in json.dumps(result)
    direct = result["explanations"]["direct"][0]
    assert [item["evidence_id"] for item in direct["profile_evidence"]] == ["cdm-e1"]
    assert direct["provenance"]["role_pack"]["external_key"] == "clinical_data_management_v1"
    assert direct["provenance"]["career_card_claim"]["kind"] == "transferable_direct"
    assert len(direct["provenance"]["jd_evidence"]) == 8
    unsupported = result["explanations"]["unsupported"][0]
    assert unsupported["provenance"]["role_pack_negative_mapping"]["text"] == "数据库锁定所有权"
    assert unsupported["provenance"]["jd_evidence"]


def test_device_and_quantitative_profiles_keep_boundaries_visible(explanation_service):
    profiles = _profiles_by_id()
    device = explanation_service.explain(
        profile=profiles["synthetic-device-application-002"],
        role_pack="medical_device_clinical_application_specialist_v1",
    )
    assert all(device["explanations"][classification] for classification in EXPLANATION_CLASSES if classification != "gap")
    assert not device["explanations"]["gap"]
    assert device["explanations"]["unsupported"][0]["provenance"]["role_pack_negative_mapping"]["text"] == "临床决策或患者照护所有权"

    quantitative = explanation_service.explain(
        profile=profiles["synthetic-cdm-quantitative-003"],
        role_pack="clinical_data_management_v1",
    )
    assert not quantitative["explanations"]["direct"]
    assert quantitative["explanations"]["transferable"]
    assert quantitative["explanations"]["partial"]
    assert quantitative["explanations"]["gap"]
    assert quantitative["explanations"]["unsupported"]


def test_explanation_rejects_non_synthetic_profiles(explanation_service):
    profile = _profiles_by_id()["synthetic-cdm-support-001"].copy()
    profile["profile_type"] = "user_confirmed"
    with pytest.raises(ValueError, match="profile_type"):
        explanation_service.explain(profile=profile, role_pack="clinical_data_management_v1")


def test_explanation_does_not_guess_rules_for_unconfigured_career_cards(explanation_service):
    profile = _profiles_by_id()["synthetic-cdm-support-001"]
    with pytest.raises(LookupError, match="no explanation match rules"):
        explanation_service.explain(profile=profile, role_pack="pharmacovigilance_drug_safety_v1")
