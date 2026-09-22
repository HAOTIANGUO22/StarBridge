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
$outputDirectory = Join-Path $projectRoot 'artifacts\dist'
$cli = Join-Path $projectRoot 'tools\arduino-cli\arduino-cli.exe'
$configDirectory = Join-Path $projectRoot 'artifacts\arduino-cli'
$config = Join-Path $configDirectory 'arduino-cli.yaml'
$boardPackage = Join-Path $projectRoot 'firmware\arduino-board-package'
$sketch = Join-Path $projectRoot 'firmware\starcore-v2'
$boardLibraries = Join-Path $sketch 'libraries'
$sharedLibraries = Join-Path $projectRoot 'firmware\shared-libraries'
$buildPath = Join-Path $env:LOCALAPPDATA 'StarBridge\build\starcore-v2'
$offlineRoot = Join-Path $pythonRoot 'src\starbridge\_offline'
$firmwareTarget = Join-Path $offlineRoot 'firmware\starcore-v2'
$runtimeTarget = Join-Path $offlineRoot 'windows-x86_64'
$arduinoData = Join-Path $env:LOCALAPPDATA 'Arduino15'
$esptoolSource = Join-Path $arduinoData 'packages\esp32\tools\esptool_py\5.3.1'
$stardustSketch = Join-Path $projectRoot 'firmware\stardust'
$stardustLibraries = Join-Path $stardustSketch 'libraries'
$stardustBuildPath = Join-Path $env:LOCALAPPDATA 'StarBridge\build\stardust'
$stardustTarget = Join-Path $offlineRoot 'firmware\stardust'
$avrdudeSource = Join-Path $arduinoData 'packages\arduino\tools\avrdude\8.0.0-arduino1'

& (Join-Path $PSScriptRoot 'bootstrap-arduino.ps1')

New-Item -ItemType Directory -Force -Path $configDirectory, $buildPath, $firmwareTarget, $runtimeTarget, $outputDirectory, $stardustBuildPath, $stardustTarget | Out-Null
& $cli config init --overwrite --dest-file $config
if ($LASTEXITCODE -ne 0) { throw 'Could not initialize the Arduino CLI build config.' }
& $cli config set directories.user $boardPackage --config-file $config
if ($LASTEXITCODE -ne 0) { throw 'Could not configure the StarBridge board package.' }

& $cli compile --config-file $config `
    --fqbn starbridge:esp32:starcore_v2 `
    --warnings all `
    --libraries $boardLibraries `
    --libraries $sharedLibraries `
    --build-path $buildPath `
    $sketch
if ($LASTEXITCODE -ne 0) { throw 'ESP32 firmware build failed.' }

& $cli compile --config-file $config `
    --fqbn starbridge:avr:stardust `
    --clean `
    --warnings all `
    --libraries $stardustLibraries `
    --libraries $sharedLibraries `
    --build-path $stardustBuildPath `
    $stardustSketch
if ($LASTEXITCODE -ne 0) { throw 'StarDust AVR firmware build failed.' }

$images = @(
    @{ offset = '0x1000'; source = 'starcore-v2.ino.bootloader.bin'; target = 'bootloader.bin' },
    @{ offset = '0x8000'; source = 'starcore-v2.ino.partitions.bin'; target = 'partitions.bin' },
    @{ offset = '0xe000'; source = 'boot_app0.bin'; target = 'boot_app0.bin' },
    @{ offset = '0x10000'; source = 'starcore-v2.ino.bin'; target = 'firmware.bin' }
)
foreach ($image in $images) {
    Copy-Item -LiteralPath (Join-Path $buildPath $image.source) `
        -Destination (Join-Path $firmwareTarget $image.target) -Force
}

Copy-Item -LiteralPath (Join-Path $esptoolSource 'esptool.exe') `
    -Destination (Join-Path $runtimeTarget 'esptool.exe') -Force
$esptoolLicenseTarget = Join-Path $runtimeTarget 'ESPTOOL_LICENSE.txt'
Copy-Item -LiteralPath (Join-Path $esptoolSource 'LICENSE') `
    -Destination $esptoolLicenseTarget -Force
$licenseText = [System.IO.File]::ReadAllText($esptoolLicenseTarget).Replace("`r`n", "`n")
[System.IO.File]::WriteAllText($esptoolLicenseTarget, $licenseText, [System.Text.UTF8Encoding]::new($false))

$stardustImage = Join-Path $stardustTarget 'firmware.hex'
Copy-Item -LiteralPath (Join-Path $stardustBuildPath 'stardust.ino.hex') `
    -Destination $stardustImage -Force
Copy-Item -LiteralPath (Join-Path $avrdudeSource 'bin\avrdude.exe') `
    -Destination (Join-Path $runtimeTarget 'avrdude.exe') -Force
Copy-Item -LiteralPath (Join-Path $avrdudeSource 'etc\avrdude.conf') `
    -Destination (Join-Path $runtimeTarget 'avrdude.conf') -Force
$avrdudeLicenseTarget = Join-Path $runtimeTarget 'AVRDUDE_LICENSE.txt'
Copy-Item -LiteralPath (Join-Path $avrdudeSource 'LICENSE.txt') `
    -Destination $avrdudeLicenseTarget -Force
$licenseText = [System.IO.File]::ReadAllText($avrdudeLicenseTarget).Replace("`r`n", "`n")
[System.IO.File]::WriteAllText($avrdudeLicenseTarget, $licenseText, [System.Text.UTF8Encoding]::new($false))

$manifest = @{
    format = 1
    board = 'starcore-v2'
    sdk_version = '4.5.0'
    firmware_version = '4.2.0'
    esp32_core_version = '3.3.11'
    esptool_version = '5.3.1'
    chip = 'esp32'
    baud = 921600
    images = @($images | ForEach-Object {
        $target = Join-Path $firmwareTarget $_.target
        @{
            offset = $_.offset
            file = $_.target
            sha256 = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    })
}
$manifest | ConvertTo-Json -Depth 5 | Set-Content `
    -LiteralPath (Join-Path $firmwareTarget 'manifest.json') -Encoding utf8

$stardustManifest = @{
    format = 1
    board = 'stardust'
    architecture = 'avr'
    sdk_version = '4.5.0'
    firmware_version = '4.3.1'
    arduino_avr_core_version = '1.8.8'
    avrdude_version = '8.0.0-arduino1'
    mcu = 'atmega328p'
    programmer = 'arduino'
    baud = 115200
    image = @{
        file = 'firmware.hex'
        sha256 = (Get-FileHash -LiteralPath $stardustImage -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}
$stardustManifest | ConvertTo-Json -Depth 5 | Set-Content `
    -LiteralPath (Join-Path $stardustTarget 'manifest.json') -Encoding utf8

& $python @pythonArgs -m build --wheel --outdir $outputDirectory $pythonRoot
if ($LASTEXITCODE -ne 0) { throw 'StarBridge wheel build failed.' }

Get-ChildItem -LiteralPath $outputDirectory -Filter 'starbridge_hardware-4.5.0-*.whl' |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1 -ExpandProperty FullName
