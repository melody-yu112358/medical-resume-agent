import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]
MANIFEST = ROOT / "data" / "evaluations" / "release-regression-manifest-v1.json"


def test_release_regression_manifest_covers_the_mvp_safety_baseline():
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "release-regression-manifest-v1"
    assert [case["case_id"] for case in payload["cases"]] == ["RR-01", "RR-02", "RR-03", "RR-04", "RR-05"]

    for case in payload["cases"]:
        fixture = case["fixture"]
        if fixture is not None:
            assert (ROOT / fixture).is_file()
        assert case["expected"].strip()
        assert case["verification_targets"]
        for target in case["verification_targets"]:
            assert (ROOT / target).is_file()


def test_release_regression_runner_lists_the_curated_targets():
    result = subprocess.run(
        [sys.executable, "scripts/run_release_regression.py", "--dry-run"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "tests/test_end_to_end_chain.py" in result.stdout
    assert "tests/test_resume_rewriter.py" in result.stdout
