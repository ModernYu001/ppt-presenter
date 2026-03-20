# Build backend exe via PyInstaller (Windows)
# Usage: powershell -ExecutionPolicy Bypass -File build_backend_exe.ps1

$ErrorActionPreference = "Stop"

if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
  python -m pip install --upgrade pyinstaller
}

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

pyinstaller --onefile --name ppt-backend run_backend.py

Write-Host "Built exe at: $root\dist\ppt-backend.exe"
