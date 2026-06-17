$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path
$backend = Join-Path $repoRoot "backend"
$python = Join-Path $backend ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Error "Backend venv not found at $python. Run: cd backend; uv venv; uv pip install pydantic pyyaml pytest"
}

Push-Location $backend
& $python -m pytest -v
$exitCode = $LASTEXITCODE
Pop-Location
exit $exitCode
