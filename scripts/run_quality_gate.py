#!/usr/bin/env python3
"""
Fixed test entry point for medical-career-agent quality gates.

Supports the following scopes:
- action3: Experience Draft, Schema, Meta example tests
- action4: Confirmation Gate positive, negative, and API tests
- action5: Role Pack Contract and Schema tests
- wave2: Action 4 + Action 5 + Action 1-3 regression
- full: All existing tests

Usage: python scripts/run_quality_gate.py [scope] [--help]
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def get_repo_root():
    """Get the medical-career-agent repository root."""
    return Path(__file__).parent.parent


def run_tests(test_files, scope_name):
    """Run pytest on the given test files."""
    repo_root = get_repo_root()
    os.chdir(repo_root)

    print(f"Running {scope_name} tests...")
    print(f"Test files: {test_files}")

    cmd = [sys.executable, "-m", "pytest"] + test_files + ["-v"]
    result = subprocess.run(cmd)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Run quality gate tests")
    parser.add_argument(
        "scope",
        nargs="?",
        choices=["action3", "action4", "action5", "wave2", "full"],
        help="Test scope to run"
    )
    parser.add_argument("--help-scope", action="store_true", help="Show scope details")

    args = parser.parse_args()

    if args.help_scope:
        print("""
Test Scopes:
- action3: Experience Draft, Schema, Meta example tests
- action4: Confirmation Gate positive, negative, and API tests
- action5: Role Pack Contract and Schema tests
- wave2: Action 4 + Action 5 + Action 1-3 regression
- full: All existing tests
""")
        return 0

    if not args.scope:
        parser.print_help()
        return 1

    # Define test scopes
    scopes = {
        "action3": [
            "tests/test_experience_draft.py",
            "tests/test_meta_analysis_example.py",
            "tests/test_schema_contracts.py"
        ],
        "action4": [
            "tests/test_confirmation_gate.py",
            "tests/test_confirmation_gate_negative.py"
        ],
        "action5": [
            "tests/test_role_pack_contracts.py",
            "tests/test_schema_contracts.py"
        ],
        "wave2": [
            "tests/test_confirmation_gate.py",
            "tests/test_confirmation_gate_negative.py",
            "tests/test_role_pack_contracts.py",
            "tests/test_experience_draft.py",
            "tests/test_meta_analysis_example.py",
            "tests/test_schema_contracts.py"
        ],
        "full": ["tests"]
    }

    if args.scope not in scopes:
        print(f"Unknown scope: {args.scope}")
        return 1

    test_files = scopes[args.scope]
    exit_code = run_tests(test_files, args.scope)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())