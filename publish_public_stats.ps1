param(
  [switch]$StatsOnly
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Invoke-Checked {
  param(
    [string]$Label,
    [scriptblock]$Command
  )
  & $Command
  if ($LASTEXITCODE -ne 0) {
    throw "$Label failed with exit code $LASTEXITCODE"
  }
}

function Invoke-AllowExitCodes {
  param(
    [string]$Label,
    [int[]]$AllowedExitCodes,
    [scriptblock]$Command
  )
  & $Command
  if ($AllowedExitCodes -notcontains $LASTEXITCODE) {
    throw "$Label failed with exit code $LASTEXITCODE"
  }
}

$PythonCandidates = @(
  "..\freqtrade\.venv\Scripts\python.exe",
  "python",
  "py"
)

$Python = $null
foreach ($Candidate in $PythonCandidates) {
  try {
    $Resolved = Get-Command $Candidate -ErrorAction Stop
    $Python = $Resolved.Source
    break
  } catch {
  }
}

if (-not $Python) {
  throw "Python was not found. Install Python or activate the freqtrade virtual environment."
}

$ExpectedLogDir = Join-Path $Root "logs"
$ExpectedLogPath = Join-Path $ExpectedLogDir "expected_vs_actual_latest.log"
New-Item -ItemType Directory -Force -Path $ExpectedLogDir | Out-Null

$Model = "entry_research_atr975_stop220_h07_h10_trail12_short35h15_lbe5_sbe10"
$ModelStatePath = Join-Path $Root "..\freqtrade\user_data\live_state\lighter_live_model_state.json"
$ReportArgs = @("..\freqtrade\lighter_expected_vs_actual_report.py", "--model", $Model, "--hours", "168")
if (Test-Path -LiteralPath $ModelStatePath) {
  try {
    $ModelState = Get-Content -LiteralPath $ModelStatePath -Raw | ConvertFrom-Json
    if ([string]$ModelState.model -eq $Model -and [string]$ModelState.promoted_at_utc) {
      $ReportArgs = @("..\freqtrade\lighter_expected_vs_actual_report.py", "--model", $Model, "--since", ([string]$ModelState.promoted_at_utc))
    }
  } catch {
  }
}

Invoke-AllowExitCodes "lighter_expected_vs_actual_report.py" @(0, 2) {
  & $Python @ReportArgs *> $ExpectedLogPath
}
Write-Host "Expected-vs-actual refreshed. Details: $ExpectedLogPath"

Invoke-Checked "export_public_stats.py" { & $Python ".\export_public_stats.py" }
Invoke-Checked "validate_public_stats.py" { & $Python ".\validate_public_stats.py" }

$Remote = git remote 2>$null
if ($LASTEXITCODE -ne 0) {
  Write-Host "Git is not initialized yet. The stats export is ready at data\stats.json."
  exit 0
}

if ($StatsOnly) {
  git add data/stats.json
} else {
  git add index.html README.md vercel.json package.json .gitignore export_public_stats.py validate_public_stats.py publish_public_stats.ps1 auto_publish_public_stats.ps1 install_auto_publish_task.ps1 data/stats.json
}

git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
  Write-Host "No public stats changes to publish."
  exit 0
}

$Stamp = Get-Date -Format "yyyy-MM-dd HH:mm"
Invoke-Checked "git commit" { git commit -m "Update public bot stats $Stamp" }

if ($Remote) {
  Invoke-Checked "git push" { git push }
} else {
  Write-Host "Committed locally. Add a GitHub remote, then run git push."
}
