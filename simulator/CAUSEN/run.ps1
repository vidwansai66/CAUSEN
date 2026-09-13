# CAUSEN AI - 1-Click PowerShell Runner
$pyPath = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
if (Test-Path $pyPath) {
    & $pyPath "$PSScriptRoot\causen_ai_simulation\main.py" @args
} else {
    python "$PSScriptRoot\causen_ai_simulation\main.py" @args
}
