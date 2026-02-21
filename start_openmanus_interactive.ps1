$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$Launcher = Join-Path $RepoRoot "openmanus_web_launcher.py"
$Port = 8765
$Url = "http://127.0.0.1:$Port"

if (-not (Test-Path $PythonExe)) {
    Write-Host "Ambiente virtual nao encontrado: $PythonExe" -ForegroundColor Red
    Write-Host "Execute primeiro a instalacao de dependencias no .venv." -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path $Launcher)) {
    Write-Host "Launcher web nao encontrado: $Launcher" -ForegroundColor Red
    exit 1
}

Write-Host "Iniciando OpenManus Interativo em $Url" -ForegroundColor Cyan
Start-Sleep -Milliseconds 400
Start-Process $Url | Out-Null
& $PythonExe $Launcher --host 127.0.0.1 --port $Port
