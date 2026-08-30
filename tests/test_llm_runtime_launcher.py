import json
from pathlib import Path

from medical_career_agent.api import _model_gateway_from_environment


ROOT = Path(__file__).resolve().parents[1]


def test_runtime_json_contains_only_non_secret_configuration():
    runtime = json.loads((ROOT / "config" / "llm.runtime.json").read_text(encoding="utf-8"))

    assert runtime["schema_version"] == "medical-resume-llm-runtime-v1"
    assert runtime["api_key_environment_variable"] == "MEDICAL_RESUME_LLM_API_KEY"
    assert runtime["base_url"].startswith("https://")
    assert 5 <= runtime["timeout_seconds"] <= 300
    assert "api_key" not in runtime


def test_launcher_uses_existing_health_contract_and_never_prints_secret():
    launcher = (ROOT / "start-with-llm.ps1").read_text(encoding="utf-8")

    assert 'resume_agent_version' in launcher
    assert 'status -eq "ok"' in launcher
    assert '$env:LLM_API_KEY = $apiKey' in launcher
    assert 'Write-Host $apiKey' not in launcher
    assert 'Write-Output $apiKey' not in launcher
    assert 'Check completed; no model or health request was made.' in launcher
    assert '[switch]$InstallDependencies' in launcher
    assert 'if (-not $InstallDependencies)' in launcher
    assert '$dependencyCheckExitCode = $LASTEXITCODE' in launcher
    assert 'pip install -e ".[resume_extract]"' in launcher
    assert 'Installing first-run dependencies' not in launcher


def test_key_setup_uses_a_hidden_prompt_and_user_environment_only():
    setup = (ROOT / "set-llm-key.ps1").read_text(encoding="utf-8")

    assert 'Read-Host "Paste API key" -AsSecureString' in setup
    assert '[EnvironmentVariableTarget]::User' in setup
    assert 'ZeroFreeBSTR' in setup
    assert 'Write-Host $plainKey' not in setup

def test_environment_timeout_is_wired_into_gateway(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "https://api.example.invalid")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "47")

    gateway = _model_gateway_from_environment()

    assert gateway is not None
    assert gateway.timeout_seconds == 47
