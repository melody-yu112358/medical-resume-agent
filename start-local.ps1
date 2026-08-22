$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $projectRoot

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCommand) {
    throw "Python 3.11+ is required. Install it from https://www.python.org/downloads/ and run this script again."
}

try {
    & $pythonCommand.Source -c "import flask, docx, pypdf" 2>$null
} catch {
    Write-Host "Installing first-run dependencies..." -ForegroundColor Cyan
    & $pythonCommand.Source -m pip install "flask>=3.0,<4" "pypdf>=5.0,<6" "python-docx>=1.1,<2"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not install Flask. Check your internet connection, then run this script again."
    }
}

$sourcePath = Join-Path $projectRoot "src"
if ($env:PYTHONPATH) {
    $env:PYTHONPATH = "$sourcePath$([IO.Path]::PathSeparator)$env:PYTHONPATH"
} else {
    $env:PYTHONPATH = $sourcePath
}

Write-Host ""
Write-Host "Medical Resume Agent is starting locally." -ForegroundColor Green
Write-Host "Open: http://127.0.0.1:5000/demo/experience-compiler/index.html" -ForegroundColor Yellow
Write-Host "Press Ctrl+C in this window when you are finished." -ForegroundColor DarkGray
Write-Host ""

& $pythonCommand.Source -c "from medical_career_agent.api import create_app; create_app().run(host='127.0.0.1', port=5000, debug=False)"
