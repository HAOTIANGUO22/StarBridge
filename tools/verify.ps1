$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonRoot = Join-Path $projectRoot 'python'
$venvPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
$python = if (Test-Path -LiteralPath $venvPython -PathType Leaf) { $venvPython } else { 'python' }

& $python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 'StarBridge requires Python 3.10 or newer.')"
if ($LASTEXITCODE -ne 0) { throw 'A supported Python interpreter was not found.' }

$previousPythonPath = $env:PYTHONPATH
try {
    $env:PYTHONPATH = Join-Path $pythonRoot 'src'
    Push-Location $pythonRoot
    try {
        & $python -m unittest discover -s tests -v
        if ($LASTEXITCODE -ne 0) { throw 'Python tests failed.' }
        & $python -m compileall -q src
        if ($LASTEXITCODE -ne 0) { throw 'Python bytecode validation failed.' }
    }
    finally {
        Pop-Location
    }
}
finally {
    $env:PYTHONPATH = $previousPythonPath
}

Write-Output 'StarBridge public SDK verification passed.'
