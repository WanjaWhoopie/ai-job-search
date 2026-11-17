# Nightly job-application pipeline — manual + Task Scheduler entry point.
# Usage:
#   .\scripts\run-pipeline.ps1                  # full run (top 5)
#   .\scripts\run-pipeline.ps1 -DryRun -Top 1   # everything except real submission
#   .\scripts\run-pipeline.ps1 -ShortlistOnly   # scrape + rank + report, no applications
#   .\scripts\run-pipeline.ps1 -Job <key|url>   # single-job smoke test
param(
    [switch]$DryRun,
    [int]$Top = 5,
    [int]$Shortlist = 30,
    [switch]$ShortlistOnly,
    [string]$Job,
    [string]$Model    # e.g. 'sonnet' or 'haiku' for a cheaper nightly run; empty = account default
)

$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
Set-Location $repo

# Master switch (toggled from the dashboard): exit quietly when scraping is off.
$configPath = Join-Path $repo 'job_scraper\config.json'
if (Test-Path $configPath) {
    $config = Get-Content $configPath -Raw | ConvertFrom-Json
    if ($config.scraping_enabled -eq $false) {
        Write-Host "Scraping is disabled (job_scraper\config.json). Toggle it on from the dashboard or set scraping_enabled: true. Exiting."
        exit 0
    }
}

$lock = Join-Path $repo 'job_scraper\.pipeline.lock'
$logDir = Join-Path $repo 'job_scraper\logs'
New-Item -ItemType Directory -Force $logDir | Out-Null

# --- Lockfile: refuse to overlap a live run; clear stale locks -------------
if (Test-Path $lock) {
    $info = Get-Content $lock -Raw | ConvertFrom-Json
    $age = (Get-Date) - [datetime]$info.started
    $alive = Get-Process -Id $info.pid -ErrorAction SilentlyContinue
    if ($alive -and $age.TotalHours -lt 3) {
        Write-Host "Pipeline already running (PID $($info.pid), started $($info.started)). Exiting."
        exit 2
    }
    Remove-Item $lock -Force
}
@{ pid = $PID; started = (Get-Date).ToString('o') } | ConvertTo-Json | Set-Content $lock -Encoding utf8

try {
    # --- PATH + tool preflight ---------------------------------------------
    . (Join-Path $PSScriptRoot 'refresh-path.ps1')
    foreach ($tool in @('claude', 'bun', 'lualatex', 'xelatex', 'python')) {
        if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
            Write-Host "FATAL: '$tool' not found on PATH. Aborting."
            exit 3
        }
    }

    # --- Cutoff: min(now + 1h45m, 23:45) -----------------------------------
    $cutoffTime = (Get-Date).AddMinutes(105)
    $hardStop = (Get-Date).Date.AddHours(23).AddMinutes(45)
    if ($cutoffTime -gt $hardStop -and (Get-Date) -lt $hardStop) { $cutoffTime = $hardStop }
    $cutoff = $cutoffTime.ToString('HH:mm')

    # --- Build the /nightly invocation -------------------------------------
    $promptArgs = "dry_run=$(($DryRun.IsPresent).ToString().ToLower()) top=$Top shortlist=$Shortlist cutoff=$cutoff"
    if ($ShortlistOnly) { $promptArgs += ' shortlist_only=true' }
    if ($Job)           { $promptArgs += " job=$Job" }

    $log = Join-Path $logDir "nightly_$(Get-Date -Format 'yyyy-MM-dd_HHmm').log"
    Write-Host "Starting pipeline: /nightly $promptArgs"
    Write-Host "Log: $log"

    # Run claude in a child process with a 2h watchdog: a laptop sleep/wake kills
    # its network connections and leaves it hung forever otherwise.
    $settingsPath = Join-Path $repo '.claude\settings.pipeline.json'
    $modelPart = if ($Model) { " --model $Model" } else { '' }
    # Strip nested-Claude-Code env vars and close stdin: a child `claude -p`
    # inheriting them (e.g. when this script is run from inside a Claude Code
    # session) hangs at startup instead of running.
    $inner = "`$env:CLAUDECODE=`$null; `$env:CLAUDE_CODE_ENTRYPOINT=`$null; `$env:CLAUDE_CODE_SSE_PORT=`$null; " +
             "`$null | & claude -p '/nightly $promptArgs' --settings '$settingsPath' --output-format text$modelPart 2>&1 | Out-File -FilePath '$log' -Encoding utf8; exit `$LASTEXITCODE"
    $proc = Start-Process powershell.exe -ArgumentList '-NoProfile', '-Command', $inner `
        -WorkingDirectory $repo -NoNewWindow -PassThru
    if (-not $proc.WaitForExit(7200000)) {
        taskkill /PID $proc.Id /T /F | Out-Null
        Add-Content $log "PIPELINE FAILURE: watchdog killed the run after 2h (hung - likely a sleep/wake cycle)"
        Write-Host "FAILED: watchdog killed a hung run after 2h. See log: $log"
        exit 5
    }
    $claudeExit = $proc.ExitCode

    # --- Post-check: the report is the contract ----------------------------
    $report = Join-Path $repo "job_scraper\reports\nightly_$(Get-Date -Format 'yyyy-MM-dd').md"
    if (-not (Test-Path $report)) {
        Add-Content $log "PIPELINE FAILURE: no report produced (claude exit $claudeExit)"
        Write-Host "FAILED: no report at $report (claude exit $claudeExit). See log."
        exit 4
    }
    Write-Host "Done. Report: $report"
    exit 0
}
finally {
    Remove-Item $lock -Force -ErrorAction SilentlyContinue
}
