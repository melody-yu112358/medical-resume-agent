#!/usr/bin/env python3
"""Validate offline standalone-Skill invariants without importing Agent/core."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_ROOT = SKILL_ROOT / "references"
DEFAULT_CASES = REFERENCE_ROOT / "standalone-eval-cases.json"
DEFAULT_RULES = REFERENCE_ROOT / "role-pack-rules.json"
PARTICIPATION_FORBIDDEN = ("主导", "独立完成", "负责整体", "管理", "领导")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES)
    args = parser.parse_args()
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    rules = json.loads(args.rules.read_text(encoding="utf-8"))
    packs = {item["role_pack"]: item for item in rules["role_packs"]}
    failures: list[str] = []
    for case in cases["cases"]:
        case_id = case["case_id"]
        text = case["candidate_text"]
        pack = packs.get(case["role_pack"])
        if pack is None:
            failures.append(f"{case_id}: unknown role pack")
            continue
        for phrase in case.get("must_include", []):
            if phrase not in text:
                failures.append(f"{case_id}: missing required phrase {phrase}")
        forbidden = list(pack["forbidden_claims"]) + list(case.get("must_not_include", []))
        if case.get("responsibility_level") == "participated":
            forbidden.extend(PARTICIPATION_FORBIDDEN)
        for phrase in sorted(set(forbidden)):
            if phrase in text:
                failures.append(f"{case_id}: forbidden phrase {phrase}")
    if failures:
        print("standalone invariant validation failed:")
        print("\n".join(failures))
        return 1
    print(f"standalone invariant validation passed: {len(cases['cases'])} cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
