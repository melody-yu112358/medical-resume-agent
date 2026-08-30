import json
from pathlib import Path


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


def test_key_setup_uses_a_hidden_prompt_and_user_environment_only():
    setup = (ROOT / "set-llm-key.ps1").read_text(encoding="utf-8")

    assert 'Read-Host "Paste API key" -AsSecureString' in setup
    assert '[EnvironmentVariableTarget]::User' in setup
    assert 'ZeroFreeBSTR' in setup
    assert 'Write-Host $plainKey' not in setup
