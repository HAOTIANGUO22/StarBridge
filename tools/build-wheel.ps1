$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonRoot = Join-Path $projectRoot 'python'
$venvPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
$python = if (Test-Path -LiteralPath $venvPython -PathType Leaf) { $venvPython } else { 'python' }
$offlineRoot = Join-Path $pythonRoot 'src\starbridge\_offline'
$firmwareRoot = Join-Path $offlineRoot 'firmware\starcore-v2'
$runtimeRoot = Join-Path $offlineRoot 'windows-x86_64'
$outputDirectory = Join-Path $projectRoot 'artifacts\dist'

$requiredFiles = @(
    (Join-Path $firmwareRoot 'bootloader.bin'),
    (Join-Path $firmwareRoot 'partitions.bin'),
    (Join-Path $firmwareRoot 'boot_app0.bin'),
    (Join-Path $firmwareRoot 'firmware.bin'),
    (Join-Path $firmwareRoot 'manifest.json'),
    (Join-Path $runtimeRoot 'esptool.exe'),
    (Join-Path $runtimeRoot 'ESPTOOL_LICENSE.txt')
)
foreach ($file in $requiredFiles) {
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) {
        throw "Required private-build artifact is missing: $file"
    }
}

$manifest = Get-Content -Raw -LiteralPath (Join-Path $firmwareRoot 'manifest.json') | ConvertFrom-Json
if ($manifest.sdk_version -ne '4.4.0') {
    throw "Firmware bundle targets SDK $($manifest.sdk_version), expected 4.4.0."
}

New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null
& $python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 'StarBridge requires Python 3.10 or newer.')"
if ($LASTEXITCODE -ne 0) { throw 'A supported Python interpreter was not found.' }

& $python -m build --wheel --outdir $outputDirectory $pythonRoot
if ($LASTEXITCODE -ne 0) { throw 'StarBridge wheel build failed.' }

Get-ChildItem -LiteralPath $outputDirectory -Filter 'starbridge_hardware-4.4.0-*.whl' |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1 -ExpandProperty FullName

