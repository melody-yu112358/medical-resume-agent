from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
EVIDENCE = ROOT / "docs" / "research" / "role-validation" / "device-clinical-application" / "candidate-evidence-v1.json"


def test_device_coverage_is_derived_only_from_explicit_ledger_qualification():
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    snapshots = evidence["jd_snapshots"]
    assert all("qualifying" in snapshot for snapshot in snapshots)
    qualifying = [snapshot for snapshot in snapshots if snapshot["qualifying"] is True]
    assert len(qualifying) == 8
    assert len({snapshot["employer"] for snapshot in qualifying}) == 8
    assert {snapshot["id"] for snapshot in snapshots if not snapshot["qualifying"]} == {
        "device-01", "device-03", "device-04", "device-05"
    }
    assert evidence["coverage"]["qualifying_jd_count"] == len(qualifying)
    assert evidence["coverage"]["qualifying_company_count"] == len({snapshot["employer"] for snapshot in qualifying})
