#!/usr/bin/env python3
"""Run a score-free synthetic Career Profile to Role Card explanation query."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from medical_career_agent.services.career_card_explanation import (  # noqa: E402
    CareerCardExplanationService,
)


DEFAULT_PROFILE_SET = ROOT / "data" / "career-map" / "career-card-explanation-test-profiles-v1.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True, help="Career-map SQLite database")
    parser.add_argument("--profile-id", required=True, help="Synthetic profile ID from the profile set")
    parser.add_argument("--role-pack", required=True, help="Current Canonical Role Pack key")
    parser.add_argument("--profile-set", type=Path, default=DEFAULT_PROFILE_SET)
    args = parser.parse_args(argv)

    profile_set = json.loads(args.profile_set.read_text(encoding="utf-8"))
    profiles = {item["profile_id"]: item for item in profile_set["profiles"]}
    try:
        profile = profiles[args.profile_id]
    except KeyError as error:
        raise SystemExit(f"Unknown synthetic profile: {args.profile_id}") from error
    result = CareerCardExplanationService(args.database).explain(
        profile=profile, role_pack=args.role_pack
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
