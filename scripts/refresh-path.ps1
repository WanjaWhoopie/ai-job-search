# Refresh PATH for MiKTeX and Bun in the current PowerShell session.
# Usage: . .\scripts\refresh-path.ps1

$userPath = [System.Environment]::GetEnvironmentVariable('Path', 'User')
$machinePath = [System.Environment]::GetEnvironmentVariable('Path', 'Machine')
$env:Path = "$machinePath;$userPath"

Write-Host "lualatex: $(if (Get-Command lualatex -ErrorAction SilentlyContinue) { (lualatex --version | Select-Object -First 1) } else { 'NOT FOUND' })"
Write-Host "xelatex:  $(if (Get-Command xelatex -ErrorAction SilentlyContinue) { (xelatex --version | Select-Object -First 1) } else { 'NOT FOUND' })"
Write-Host "bun:      $(if (Get-Command bun -ErrorAction SilentlyContinue) { (bun --version) } else { 'NOT FOUND' })"
