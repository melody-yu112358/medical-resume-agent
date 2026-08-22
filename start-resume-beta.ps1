$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $projectRoot

python -c "import sys; sys.path.insert(0, 'src'); from medical_career_agent.api import create_app; create_app().run(host='127.0.0.1', port=5000, debug=False)"
