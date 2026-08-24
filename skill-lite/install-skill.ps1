$ErrorActionPreference = "Stop"

$skillSource = Join-Path $PSScriptRoot "medical-resume-skill"
if (-not (Test-Path -LiteralPath (Join-Path $skillSource "SKILL.md"))) {
    throw "medical-resume-skill was not found next to this installer. Run the script from the cloned repository."
}

$codexRoot = Join-Path $env:USERPROFILE ".codex"
$skillsRoot = Join-Path $codexRoot "skills"
$skillTarget = Join-Path $skillsRoot "medical-resume-skill"

New-Item -ItemType Directory -Force -Path $skillsRoot | Out-Null
New-Item -ItemType Directory -Force -Path $skillTarget | Out-Null
Get-ChildItem -LiteralPath $skillSource -Force | Copy-Item -Destination $skillTarget -Recurse -Force

Write-Host "Installed Medical Resume Skill Lite to:" -ForegroundColor Green
Write-Host $skillTarget -ForegroundColor Yellow
Write-Host "Start a new Codex conversation, then ask Codex to use medical-resume-skill for a real experience and target direction." -ForegroundColor Cyan
