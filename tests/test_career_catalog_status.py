"""The public inventory is a reproducible projection, not a second manual count."""
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from generate_career_catalog_status import OUTPUT, render


def test_committed_status_matches_sources():
    assert (ROOT / OUTPUT).read_text(encoding="utf-8") == render(ROOT)


@pytest.fixture
def sources(tmp_path):
    for relative in ("data/role-packs", "data/career_cards", "data/careers", "data/career-map",
                     "skill-lite/medical-resume-skill/references"):
        shutil.copytree(ROOT / relative, tmp_path / relative)
    return tmp_path


def test_rule_removal_updates_inventory_without_changing_other_sources(sources):
    before = render(sources)
    path = sources / "data/career-map/career-card-match-rules-v1.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["rules"].pop()
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    after = render(sources)
    assert before != after
    assert f"/ {len(data['rules'])} |" in after
    assert after == render(sources)
    assert not (sources / OUTPUT).exists()


def test_bad_card_reference_is_rejected(sources):
    path = sources / "data/career-map/career-card-match-rules-v1.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["rules"][0]["career_card_id"] = "missing-card"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="rule Card reference mismatch"):
        render(sources)
