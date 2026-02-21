$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$DesktopApp = Join-Path $RepoRoot "openmanus_desktop_app.py"

if (-not (Test-Path $PythonExe)) {
    Write-Host "Ambiente virtual nao encontrado: $PythonExe" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $DesktopApp)) {
    Write-Host "App desktop nao encontrado: $DesktopApp" -ForegroundColor Red
    exit 1
}

Write-Host "Iniciando OpenManus Desktop..." -ForegroundColor Cyan
& $PythonExe $DesktopApp
