$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonRoot = Join-Path $projectRoot 'python'
$previousPythonPath = $env:PYTHONPATH
try {
    $env:PYTHONPATH = Join-Path $pythonRoot 'src'
    Push-Location $pythonRoot
    try {
        python -m unittest discover -s tests -v
        if ($LASTEXITCODE -ne 0) { throw 'Python tests failed.' }
        python -m compileall -q src
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
