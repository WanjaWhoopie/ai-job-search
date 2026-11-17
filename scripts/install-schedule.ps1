# Register (or remove) the nightly pipeline as a Windows Scheduled Task.
# Usage:
#   .\scripts\install-schedule.ps1              # install: daily 22:00
#   .\scripts\install-schedule.ps1 -Uninstall
param(
    [switch]$Uninstall,
    [string]$At = '22:00'
)

$taskName = 'AI-JobSearch-Nightly'

if ($Uninstall) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "Removed scheduled task '$taskName'."
    exit 0
}

$repo = Split-Path $PSScriptRoot -Parent

# Python dependency for scripts/submit_app.py
python -m pip install -q -r (Join-Path $PSScriptRoot 'requirements.txt')

$action = New-ScheduledTaskAction -Execute 'powershell.exe' `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$repo\scripts\run-pipeline.ps1`"" `
    -WorkingDirectory $repo
$trigger = New-ScheduledTaskTrigger -Daily -At $At
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
    -StartWhenAvailable -WakeToRun -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

# Interactive logon (default): the claude CLI's login lives in this user's profile.
# Logged-on-but-locked works; fully logged out at 22:00 means the run is skipped
# (-StartWhenAvailable catches a later logon the same night).
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger `
    -Settings $settings -Description 'Nightly autonomous job application pipeline' -Force | Out-Null

Write-Host "Registered '$taskName' - daily at $At, 2h execution limit."
Write-Host "Trigger a run now with:  Start-ScheduledTask $taskName"
Write-Host "Check last result with:  (Get-ScheduledTaskInfo $taskName).LastTaskResult"
