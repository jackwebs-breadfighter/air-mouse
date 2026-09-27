@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo 搵唔到虛擬環境,請先執行 install.ps1
    echo 例如: powershell -ExecutionPolicy Bypass -File install.ps1
    pause
    exit /b 1
)
".venv\Scripts\python.exe" server.py
pause
