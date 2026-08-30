param(
    [string]$EnvironmentVariableName = "MEDICAL_RESUME_LLM_API_KEY"
)

$ErrorActionPreference = "Stop"

if ($EnvironmentVariableName -notmatch '^[A-Z_][A-Z0-9_]*$') {
    throw "Environment variable name must contain only uppercase letters, digits, and underscores."
}

Write-Host "This stores the API key in your current Windows user environment." -ForegroundColor Cyan
Write-Host "The key will not be written to this repository or printed to the terminal." -ForegroundColor DarkGray
$secureKey = Read-Host "Paste API key" -AsSecureString

if ($secureKey.Length -eq 0) {
    throw "API key cannot be empty."
}

$secretPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
try {
    $plainKey = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($secretPointer)
    [Environment]::SetEnvironmentVariable(
        $EnvironmentVariableName,
        $plainKey,
        [EnvironmentVariableTarget]::User
    )
} finally {
    if ($secretPointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($secretPointer)
    }
    $plainKey = $null
    $secureKey.Dispose()
}

Write-Host "Saved $EnvironmentVariableName for the current Windows user." -ForegroundColor Green
Write-Host "Open a new PowerShell window, then run .\start-with-llm.ps1" -ForegroundColor Yellow
