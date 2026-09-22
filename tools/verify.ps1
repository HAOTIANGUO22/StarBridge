$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonRoot = Join-Path $projectRoot 'python'
$venvPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
$python = if (Test-Path -LiteralPath $venvPython -PathType Leaf) { $venvPython } else { 'python' }
$pythonArgs = @()
if ($python -eq 'python') {
    & $python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
    if ($LASTEXITCODE -ne 0 -and (Get-Command py -ErrorAction SilentlyContinue)) {
        $python = 'py'
        $pythonArgs = @('-3.13')
    }
}
$firmwareSketch = Join-Path $projectRoot 'firmware\starcore-v2'
$boardLibraries = Join-Path $firmwareSketch 'libraries'
$sharedLibraries = Join-Path $projectRoot 'firmware\shared-libraries'
$boardPackageRoot = Join-Path $projectRoot 'firmware\arduino-board-package'
$arduinoConfigDirectory = Join-Path $projectRoot 'artifacts\arduino-cli'
$arduinoConfig = Join-Path $arduinoConfigDirectory 'arduino-cli.yaml'
$arduinoCli = Join-Path $projectRoot 'tools\arduino-cli\arduino-cli.exe'
$firmwareBuildPath = Join-Path $env:LOCALAPPDATA 'StarBridge\verify\starcore-v2'
$stardustSketch = Join-Path $projectRoot 'firmware\stardust'
$stardustLibraries = Join-Path $stardustSketch 'libraries'
$stardustBuildPath = Join-Path $env:LOCALAPPDATA 'StarBridge\verify\stardust'

& (Join-Path $PSScriptRoot 'bootstrap-arduino.ps1')

& $python @pythonArgs -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 'StarBridge requires Python 3.10 or newer.')"
if ($LASTEXITCODE -ne 0) { throw 'A supported Python interpreter was not found.' }

$previousPythonPath = $env:PYTHONPATH
try {
    $env:PYTHONPATH = Join-Path $pythonRoot 'src'
    Push-Location $pythonRoot
    try {
        & $python @pythonArgs -m unittest discover -s tests -v
        if ($LASTEXITCODE -ne 0) { throw 'Python tests failed.' }
        & $python @pythonArgs -m compileall -q src
        if ($LASTEXITCODE -ne 0) { throw 'Python bytecode validation failed.' }
    }
    finally {
        Pop-Location
    }

    New-Item -ItemType Directory -Force -Path $arduinoConfigDirectory | Out-Null
    & $arduinoCli config init --overwrite --dest-file $arduinoConfig
    if ($LASTEXITCODE -ne 0) { throw 'Could not create Arduino CLI config.' }
    & $arduinoCli config set directories.user $boardPackageRoot --config-file $arduinoConfig
    if ($LASTEXITCODE -ne 0) { throw 'Could not configure the StarBridge board package.' }

    & $arduinoCli compile --config-file $arduinoConfig `
        --fqbn starbridge:esp32:starcore_v2 `
        --warnings all `
        --libraries $boardLibraries `
        --libraries $sharedLibraries `
        --build-path $firmwareBuildPath `
        $firmwareSketch
    if ($LASTEXITCODE -ne 0) { throw 'ESP32 firmware build failed.' }

    & $arduinoCli compile --config-file $arduinoConfig `
        --fqbn starbridge:avr:stardust `
        --clean `
        --warnings all `
        --libraries $stardustLibraries `
        --libraries $sharedLibraries `
        --build-path $stardustBuildPath `
        $stardustSketch
    if ($LASTEXITCODE -ne 0) { throw 'StarDust AVR firmware build failed.' }
}
finally {
    $env:PYTHONPATH = $previousPythonPath
}

Write-Output 'StarBridge SDK, StarCore V2 and StarDust firmware verification passed.'
