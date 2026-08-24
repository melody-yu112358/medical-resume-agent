[CmdletBinding()]
param(
    [string]$DestinationRoot = (Join-Path (Join-Path $env:USERPROFILE ".codex") "skills")
)

$ErrorActionPreference = "Stop"

$skillSource = Join-Path $PSScriptRoot "medical-resume-skill"
if (-not (Test-Path -LiteralPath (Join-Path $skillSource "SKILL.md"))) {
    throw "medical-resume-skill was not found next to this installer. Run the script from the cloned repository."
}

$skillsRoot = $DestinationRoot
$skillTarget = Join-Path $skillsRoot "medical-resume-skill"
$stagingTarget = Join-Path $skillsRoot "medical-resume-skill.installing"

New-Item -ItemType Directory -Force -Path $skillsRoot | Out-Null

# Copy the source *contents* into a fresh staging directory. Copying the source
# directory onto an existing target can create medical-resume-skill/medical-resume-skill.
if (Test-Path -LiteralPath $stagingTarget) {
    Remove-Item -LiteralPath $stagingTarget -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $stagingTarget | Out-Null
Get-ChildItem -LiteralPath $skillSource -Force | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $stagingTarget -Recurse -Force
}

if (-not (Test-Path -LiteralPath (Join-Path $stagingTarget "SKILL.md"))) {
    throw "Staged skill is incomplete: SKILL.md is missing."
}
if (Test-Path -LiteralPath $skillTarget) {
    Remove-Item -LiteralPath $skillTarget -Recurse -Force
}
Move-Item -LiteralPath $stagingTarget -Destination $skillTarget

Write-Host "Installed Medical Resume Skill Lite to:" -ForegroundColor Green
Write-Host $skillTarget -ForegroundColor Yellow
Write-Host "Start a new Codex conversation, then ask Codex to use medical-resume-skill for a real experience and target direction." -ForegroundColor Cyan
