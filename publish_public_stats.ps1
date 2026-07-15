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
