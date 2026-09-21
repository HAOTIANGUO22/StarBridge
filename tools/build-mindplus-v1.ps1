$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
$python = if (Test-Path -LiteralPath $venvPython) { $venvPython } else { "python" }

& $python (Join-Path $PSScriptRoot "build-mindplus-v1.py")
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
