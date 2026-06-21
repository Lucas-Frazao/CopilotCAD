# Note: no `$ErrorActionPreference = "Stop"` here — npm/vite write harmless
# deprecation notices to stderr, which under Stop would abort the script even on
# success. We gate on $LASTEXITCODE from each command instead.
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path
$frontend = Join-Path $repoRoot "frontend"

if (-not (Test-Path (Join-Path $frontend "node_modules"))) {
    Write-Host "frontend/node_modules not found. Run: cd frontend; npm install" -ForegroundColor Red
    exit 1
}

Push-Location $frontend
npm run typecheck
$code = $LASTEXITCODE
if ($code -eq 0) {
    npm test
    $code = $LASTEXITCODE
}
Pop-Location
exit $code
