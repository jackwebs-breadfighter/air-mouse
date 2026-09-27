<#
.SYNOPSIS
  Builds AirMouse.exe - a single self-contained executable that end users
  can run without installing Python themselves.
#>
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "搵唔到 .venv,請先執行 install.ps1" -ForegroundColor Yellow
    exit 1
}

& ".\.venv\Scripts\python.exe" -m pip show pyinstaller *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "安裝 PyInstaller..."
    & ".\.venv\Scripts\python.exe" -m pip install pyinstaller -q
}

Remove-Item build, dist -Recurse -Force -ErrorAction SilentlyContinue
& ".\.venv\Scripts\python.exe" -m PyInstaller AirMouse.spec

Write-Host ""
Write-Host "完成! 執行檔喺: dist\AirMouse.exe" -ForegroundColor Green
Write-Host "呢個 exe 可以獨立分享畀人,唔使裝 Python。" -ForegroundColor Green
