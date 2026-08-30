param(
    [string]$ConfigPath = "config\llm.runtime.json",
    [ValidateRange(1, 65535)]
    [int]$Port = 5000,
    [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $projectRoot

$resolvedConfig = Join-Path $projectRoot $ConfigPath
if (-not (Test-Path -LiteralPath $resolvedConfig -PathType Leaf)) {
    throw "LLM runtime config not found: $resolvedConfig"
}

try {
    $runtime = Get-Content -Raw -LiteralPath $resolvedConfig | ConvertFrom-Json
} catch {
    throw "LLM runtime config is not valid JSON: $resolvedConfig"
}

if ($runtime.schema_version -ne "medical-resume-llm-runtime-v1") {
    throw "Unsupported LLM runtime config schema_version."
}

$baseUrl = [string]$runtime.base_url
$model = [string]$runtime.model
$keyVariable = [string]$runtime.api_key_environment_variable
$timeoutSeconds = [int]$runtime.timeout_seconds

if (-not [Uri]::IsWellFormedUriString($baseUrl, [UriKind]::Absolute)) {
    throw "base_url must be an absolute URL."
}
if ([string]::IsNullOrWhiteSpace($model)) {
    throw "model cannot be empty."
}
if ($keyVariable -notmatch '^[A-Z_][A-Z0-9_]*$') {
    throw "api_key_environment_variable is invalid."
}
if ($timeoutSeconds -lt 5 -or $timeoutSeconds -gt 300) {
    throw "timeout_seconds must be between 5 and 300."
}

$apiKey = [Environment]::GetEnvironmentVariable($keyVariable, "Process")
if ([string]::IsNullOrWhiteSpace($apiKey)) {
    $apiKey = [Environment]::GetEnvironmentVariable($keyVariable, "User")
}
if ([string]::IsNullOrWhiteSpace($apiKey)) {
    $apiKey = [Environment]::GetEnvironmentVariable($keyVariable, "Machine")
}
if ([string]::IsNullOrWhiteSpace($apiKey)) {
    throw "API key environment variable '$keyVariable' is missing. Run .\set-llm-key.ps1 first."
}

# Map versioned, non-secret settings and the user-scoped secret into the
# process-only variable names consumed by the Flask application.
$env:LLM_BASE_URL = $baseUrl
$env:LLM_API_KEY = $apiKey
$env:LLM_MODEL = $model
$env:LLM_TIMEOUT_SECONDS = [string]$timeoutSeconds
$env:MEDICAL_RESUME_PORT = [string]$Port

Write-Host "LLM configuration is ready." -ForegroundColor Green
Write-Host "Provider: $($runtime.provider)" -ForegroundColor DarkGray
Write-Host "Model: $model" -ForegroundColor DarkGray
Write-Host "Base URL: $baseUrl" -ForegroundColor DarkGray
Write-Host "API key source: user/process environment variable $keyVariable" -ForegroundColor DarkGray

if ($CheckOnly) {
    Write-Host "Check completed; no model or health request was made." -ForegroundColor Yellow
    exit 0
}

# Refuse to hide an old or unrelated listener behind a second launch attempt.
$healthUrl = "http://127.0.0.1:$Port/api/health"
try {
    $existingHealth = Invoke-RestMethod -Uri $healthUrl -Method Get -TimeoutSec 2
    if ($existingHealth.status -eq "ok" -and $existingHealth.resume_agent_version) {
        Write-Host "Medical Resume Agent is already running ($($existingHealth.resume_agent_version))." -ForegroundColor Green
        Write-Host "Open: http://127.0.0.1:$Port/" -ForegroundColor Yellow
        exit 0
    }
    throw "Port $Port is occupied by an unrelated or incompatible service."
} catch {
    if ($_.Exception.Message -like "Port $Port is occupied*") {
        throw
    }
    $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($listener) {
        throw "Port $Port is already in use by another process. Stop that process or choose another port with -Port."
    }
}

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCommand) {
    throw "Python 3.11+ is required."
}

try {
    & $pythonCommand.Source -c "import flask, docx, pypdf" 2>$null
} catch {
    Write-Host "Installing first-run dependencies..." -ForegroundColor Cyan
    & $pythonCommand.Source -m pip install "flask>=3.0,<4" "pypdf>=5.0,<6" "python-docx>=1.1,<2"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not install required Python packages."
    }
}

$sourcePath = Join-Path $projectRoot "src"
if ($env:PYTHONPATH) {
    $env:PYTHONPATH = "$sourcePath$([IO.Path]::PathSeparator)$env:PYTHONPATH"
} else {
    $env:PYTHONPATH = $sourcePath
}

Write-Host ""
Write-Host "Medical Resume Agent is starting with LLM support." -ForegroundColor Green
Write-Host "Open: http://127.0.0.1:$Port/" -ForegroundColor Yellow
Write-Host "Press Ctrl+C when you are finished." -ForegroundColor DarkGray
Write-Host ""

& $pythonCommand.Source -c "import os; from medical_career_agent.api import create_app; create_app().run(host='127.0.0.1', port=int(os.environ['MEDICAL_RESUME_PORT']), debug=False)"
