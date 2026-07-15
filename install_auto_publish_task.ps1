$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$TaskName = "Lighter Public Stats Publisher"
$ScriptPath = Join-Path $Root "auto_publish_public_stats.ps1"

if (-not (Test-Path $ScriptPath)) {
  throw "Missing auto publisher script: $ScriptPath"
}

$Action = New-ScheduledTaskAction `
  -Execute "powershell.exe" `
  -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$ScriptPath`""

$Trigger = New-ScheduledTaskTrigger `
  -Once `
  -At (Get-Date).AddMinutes(1) `
  -RepetitionInterval (New-TimeSpan -Minutes 1)

$Settings = New-ScheduledTaskSettingsSet `
  -StartWhenAvailable `
  -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries `
  -MultipleInstances IgnoreNew

Register-ScheduledTask `
  -TaskName $TaskName `
  -Action $Action `
  -Trigger $Trigger `
  -Settings $Settings `
  -Description "Publishes sanitized Lighter BTC bot public stats every minute." `
  -Force | Out-Null

Get-ScheduledTaskInfo -TaskName $TaskName | Format-List LastRunTime,NextRunTime,LastTaskResult,NumberOfMissedRuns
