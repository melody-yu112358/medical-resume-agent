"""Run the small, deterministic release-regression baseline.

This is intentionally narrower than the full suite. Use it before reviewing a
change that may affect the evidence boundary or candidate-facing wording; run
the full test suite before release as well.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "data" / "evaluations" / "release-regression-manifest-v1.json"


def load_targets(manifest_path: Path) -> list[str]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "release-regression-manifest-v1":
        raise ValueError("unsupported release-regression manifest version")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("release-regression manifest must contain cases")

    targets: list[str] = []
    for case in cases:
        for target in case.get("verification_targets", []):
            if target not in targets:
                targets.append(target)
    if not targets:
        raise ValueError("release-regression manifest contains no verification targets")
    return targets


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the MVP release-regression baseline")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--dry-run", action="store_true", help="Print the selected tests without running pytest")
    args = parser.parse_args()
    manifest = args.manifest.resolve()
    targets = load_targets(manifest)
    for target in targets:
        if not (ROOT / target).is_file():
            raise FileNotFoundError(f"verification target does not exist: {target}")

    command = [sys.executable, "-m", "pytest", "-q", *targets]
    print("Release-regression baseline:", manifest.relative_to(ROOT))
    print("Command:", " ".join(command))
    if args.dry_run:
        return 0
    return subprocess.run(command, cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
