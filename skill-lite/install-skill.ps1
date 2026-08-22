$ErrorActionPreference = "Stop"

$skillSource = Join-Path $PSScriptRoot "medical-resume-skill"
if (-not (Test-Path -LiteralPath (Join-Path $skillSource "SKILL.md"))) {
    throw "medical-resume-skill was not found next to this installer. Run the script from the cloned repository."
}

$codexRoot = Join-Path $env:USERPROFILE ".codex"
$skillsRoot = Join-Path $codexRoot "skills"
$skillTarget = Join-Path $skillsRoot "medical-resume-skill"

New-Item -ItemType Directory -Force -Path $skillsRoot | Out-Null
Copy-Item -LiteralPath $skillSource -Destination $skillTarget -Recurse -Force

Write-Host "Installed Medical Resume Skill Lite to:" -ForegroundColor Green
Write-Host $skillTarget -ForegroundColor Yellow
Write-Host "Start a new Codex conversation, then ask: 请用 medical-resume-skill 帮我整理这段经历，目标是医学事务 / MSL。" -ForegroundColor Cyan
