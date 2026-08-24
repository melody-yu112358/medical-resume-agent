from __future__ import annotations

import shutil
import subprocess
import uuid
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "skill-lite" / "install-skill.ps1"
SOURCE = ROOT / "skill-lite" / "medical-resume-skill"


def _powershell() -> str:
    executable = shutil.which("pwsh") or shutil.which("powershell")
    if not executable:
        pytest.skip("PowerShell is required to validate the Windows installer")
    return executable


def _install(destination_root: Path) -> None:
    subprocess.run(
        [
            _powershell(),
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(INSTALLER),
            "-DestinationRoot",
            str(destination_root),
        ],
        check=True,
        capture_output=True,
    )


def test_windows_skill_reinstall_updates_in_place_without_nesting():
    # Keep the test directory inside the repository to avoid Windows profiles
    # whose non-ASCII temp path is unavailable to the active Python runtime.
    test_root = ROOT / ".test-artifacts" / f"skill-install-{uuid.uuid4().hex}"
    skills_root = test_root / "skills"
    target = skills_root / "medical-resume-skill"
    try:
        _install(skills_root)
        assert (target / "SKILL.md").is_file()

        # Simulate an outdated installed reference and verify reinstall replaces it.
        installed_prompt = target / "references" / "prompt-templates.md"
        installed_prompt.write_text("outdated", encoding="utf-8")
        _install(skills_root)

        assert (target / "SKILL.md").is_file()
        assert not (target / "medical-resume-skill").exists()
        for reference in ("prompt-templates.md", "dense-resume-protocol.md"):
            assert (target / "references" / reference).read_bytes() == (
                SOURCE / "references" / reference
            ).read_bytes()
    finally:
        shutil.rmtree(test_root, ignore_errors=True)
