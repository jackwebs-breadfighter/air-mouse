<#
.SYNOPSIS
  Optional one-time setup for AirMouse.exe users (no Python/source needed):
  opens the firewall port and configures the exe to auto-start at every
  Windows login - elevated (so it can also control elevated windows like
  Task Manager), hidden (no console window), and auto-restarting if it ever
  crashes or gets closed.

  Run this AS ADMINISTRATOR (right-click this file's PowerShell shortcut, or
  right-click PowerShell itself, and choose "Run as administrator"), once.
  Place it in the same folder as AirMouse.exe first.
#>
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$exePath = Join-Path $ScriptDir "AirMouse.exe"

if (-not (Test-Path $exePath)) {
    Write-Host "搵唔到 AirMouse.exe,請將呢個 script 放喺同一個資料夾。" -ForegroundColor Red
    exit 1
}

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "呢個 script 要用管理員身份行。請右鍵 PowerShell -> 「以系統管理員身分執行」,再嚟一次。" -ForegroundColor Red
    exit 1
}

# Read the port from config.json if it already exists (first run creates it),
# so the firewall rule matches whatever port is actually in use.
$configPath = Join-Path $ScriptDir "config.json"
$port = 8765
if (Test-Path $configPath) {
    try {
        $cfg = Get-Content $configPath -Raw | ConvertFrom-Json
        if ($cfg.port) { $port = [int]$cfg.port }
    } catch {}
}

$ruleName = "AirMouse (Private, TCP $port)"
$existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
if (-not $existingRule) {
    New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Action Allow -Protocol TCP -LocalPort $port -Profile Private | Out-Null
    Write-Host "已加入防火牆規則 (只限 Private network, port $port)。" -ForegroundColor Green
} else {
    Write-Host "防火牆規則已經存在,跳過。"
}

$taskName = "AirMouse"
$action = New-ScheduledTaskAction -Execute $exePath -Argument "--background" -WorkingDirectory $ScriptDir
$trigger = New-ScheduledTaskTrigger -AtLogOn
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable `
    -Hidden -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1)
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings | Out-Null
Start-ScheduledTask -TaskName $taskName

Write-Host ""
Write-Host "設定完成! AirMouse 而家已經以管理員身份喺背景行緊,並且會喺每次" -ForegroundColor Green
Write-Host "開機登入之後自動啟動、斷咗會自動重新啟動。" -ForegroundColor Green
