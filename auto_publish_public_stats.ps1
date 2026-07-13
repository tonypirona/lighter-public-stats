$ErrorActionPreference = "Continue"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogDir = Join-Path $Root "logs"
$LogPath = Join-Path $LogDir "auto_publish.log"
$LockPath = Join-Path $Root "auto_publish.lock"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Write-AutoLog {
  param([string]$Message)
  $Stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  Add-Content -Path $LogPath -Value "[$Stamp] $Message"
}

$LockStream = $null
try {
  $LockStream = [System.IO.File]::Open($LockPath, "OpenOrCreate", "ReadWrite", "None")
} catch {
  Write-AutoLog "Skipped: another publish run is already active."
  exit 0
}

try {
  Set-Location $Root
  Write-AutoLog "Starting public stats publish."
  $Output = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root "publish_public_stats.ps1") 2>&1
  $ExitCode = $LASTEXITCODE
  foreach ($Line in $Output) {
    Write-AutoLog "  $Line"
  }
  if ($ExitCode -ne 0) {
    throw "publish_public_stats.ps1 exited with code $ExitCode"
  }
  Write-AutoLog "Finished public stats publish."
} catch {
  Write-AutoLog "ERROR: $($_.Exception.Message)"
  exit 1
} finally {
  if ($LockStream) {
    $LockStream.Close()
    $LockStream.Dispose()
  }
  Remove-Item $LockPath -ErrorAction SilentlyContinue
}
