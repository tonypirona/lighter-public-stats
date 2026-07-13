$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

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

& $Python ".\export_public_stats.py"

$Remote = git remote 2>$null
if ($LASTEXITCODE -ne 0) {
  Write-Host "Git is not initialized yet. The stats export is ready at data\stats.json."
  exit 0
}

git add index.html README.md vercel.json package.json .gitignore export_public_stats.py publish_public_stats.ps1 auto_publish_public_stats.ps1 data/stats.json

$Status = git status --porcelain
if (-not $Status) {
  Write-Host "No public stats changes to publish."
  exit 0
}

$Stamp = Get-Date -Format "yyyy-MM-dd HH:mm"
git commit -m "Update public bot stats $Stamp"

if ($Remote) {
  git push
} else {
  Write-Host "Committed locally. Add a GitHub remote, then run git push."
}
