from __future__ import annotations

import hashlib
import json
from pathlib import Path


EVIDENCE = Path(__file__).parents[1] / "docs" / "research" / "role-validation" / "cdm" / "candidate-evidence-v1.json"


def test_qualifying_cdm_digest_is_recomputable_from_retained_inputs():
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert "url + LF" in evidence["provenance_policy"]["source_digest_basis"]
    qualifying = [snapshot for snapshot in evidence["jd_snapshots"] if snapshot["qualifying"]]
    assert len(qualifying) == 8
    for snapshot in qualifying:
        payload = f'{snapshot["url"]}\n{snapshot["source_snapshot"]}'.encode("utf-8")
        expected = "sha256:" + hashlib.sha256(payload).hexdigest()
        assert snapshot["source_digest_scope"] == "url_plus_lf_plus_source_snapshot_utf8_v1"
        assert snapshot["source_digest"] == expected
