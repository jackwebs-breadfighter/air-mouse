<#
.SYNOPSIS
  Sets up AirMouse: checks Python, creates a venv, installs dependencies,
  and opens a Windows Firewall rule limited to the Private network profile.
#>

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "== AirMouse 安裝程式 ==" -ForegroundColor Cyan

# 1. Find Python 3.12+
function Get-PythonCmd {
    foreach ($candidate in @(
        @{ Exe = "py"; Args = @("-3.12") },
        @{ Exe = "py"; Args = @("-3") },
        @{ Exe = "python"; Args = @() }
    )) {
        try {
            $verOutput = & $candidate.Exe @($candidate.Args) --version 2>$null
            if ($LASTEXITCODE -eq 0 -and $verOutput -match "Python (\d+)\.(\d+)") {
                $major = [int]$Matches[1]; $minor = [int]$Matches[2]
                if ($major -gt 3 -or ($major -eq 3 -and $minor -ge 12)) {
                    return $candidate
                }
            }
        } catch {}
    }
    return $null
}

$pythonCmd = Get-PythonCmd
if (-not $pythonCmd) {
    Write-Host "搵唔到 Python 3.12 或以上版本。" -ForegroundColor Yellow
    Write-Host "請先行以下指令安裝,然後重新執行呢個 script:" -ForegroundColor Yellow
    Write-Host "  winget install Python.Python.3.12" -ForegroundColor White
    exit 1
}
Write-Host ("使用 Python: {0} {1}" -f $pythonCmd.Exe, ($pythonCmd.Args -join " "))

# 2. Create venv
$venvPath = Join-Path $ScriptDir ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "建立虛擬環境 (.venv)..."
    & $pythonCmd.Exe @($pythonCmd.Args) -m venv $venvPath
} else {
    Write-Host "虛擬環境已經存在,跳過。"
}

$venvPython = Join-Path $venvPath "Scripts\python.exe"

# 3. Install dependencies
Write-Host "安裝依賴 (aiohttp, qrcode)..."
& $venvPython -m pip install --upgrade pip -q
& $venvPython -m pip install -r (Join-Path $ScriptDir "requirements.txt") -q
Write-Host "依賴安裝完成。" -ForegroundColor Green

# 4. Firewall rule (Private profile only) - needs admin
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

# Read (or generate) the port from config.json so the firewall rule matches it.
$configPath = Join-Path $ScriptDir "config.json"
$port = 8765
if (Test-Path $configPath) {
    try {
        $cfg = Get-Content $configPath -Raw | ConvertFrom-Json
        if ($cfg.port) { $port = [int]$cfg.port }
    } catch {}
}

$ruleName = "AirMouse (Private, TCP $port)"
if ($isAdmin) {
    $existing = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
    if (-not $existing) {
        Write-Host "加入防火牆規則 (只限 Private network, port $port)..."
        New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Action Allow `
            -Protocol TCP -LocalPort $port -Profile Private | Out-Null
        Write-Host "防火牆規則已加入。" -ForegroundColor Green
    } else {
        Write-Host "防火牆規則已經存在,跳過。"
    }
} else {
    Write-Host "未有管理員權限,略過防火牆規則設定。" -ForegroundColor Yellow
    Write-Host "如果手機連唔到,請以管理員身份執行 PowerShell,再手動行:" -ForegroundColor Yellow
    Write-Host ("  New-NetFirewallRule -DisplayName '{0}' -Direction Inbound -Action Allow -Protocol TCP -LocalPort {1} -Profile Private" -f $ruleName, $port) -ForegroundColor White
}

# 5. Optional: Task Scheduler auto-start at logon, elevated.
# Runs as Administrator so it can also control elevated windows (Task Manager,
# admin PowerShell, installers, etc.) - Windows blocks simulated input from a
# normal process to an elevated one (UIPI). A Task Scheduler task set to
# "highest privileges" elevates silently on every run - no UAC prompt after
# this one-time setup, unlike double-clicking start.bat and choosing
# "Run as administrator" (which prompts every single time).
$answer = Read-Host "要唔要設定開機登入後自動以管理員身份啟動? (y/N)"
if ($answer -match "^(y|Y)") {
    $taskName = "AirMouse"
    # Launch python.exe directly with --background (skips the banner/QR and
    # runs the server in the foreground of THIS process) rather than through
    # start.bat/cmd.exe:
    #   - No console window at all (-Hidden), so there's nothing to
    #     accidentally click into and freeze (cmd's QuickEdit mode pauses the
    #     whole console, and everything running in it, on a stray click).
    #   - Task Scheduler directly supervises the real server process, so
    #     -RestartCount/-RestartInterval below can actually catch a crash or
    #     an accidental "End Task" and bring it back up automatically.
    # pythonw.exe (not python.exe): Task Scheduler's "Hidden" setting below
    # only hides the TASK from the Task Scheduler list - for an "Interactive"
    # logon-type action it still opens a real, visible console for a
    # console-subsystem exe. pythonw.exe is GUI-subsystem and never gets one.
    $venvPythonw = Join-Path $ScriptDir ".venv\Scripts\pythonw.exe"
    $serverScript = Join-Path $ScriptDir "server.py"
    $action = New-ScheduledTaskAction -Execute $venvPythonw -Argument "`"$serverScript`" --background" -WorkingDirectory $ScriptDir
    $trigger = New-ScheduledTaskTrigger -AtLogOn
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable `
        -Hidden -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1)
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings | Out-Null
    Start-ScheduledTask -TaskName $taskName
    Write-Host "已設定開機自動以管理員身份啟動,並已即刻啟動 (工作排程器: $taskName)。" -ForegroundColor Green
}

Write-Host ""
Write-Host "安裝完成! 雙擊 start.bat 啟動 AirMouse。" -ForegroundColor Cyan
