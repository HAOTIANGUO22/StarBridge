$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$cliVersion = '1.5.1'
$cliSha256 = 'FABE42E0EB04D00E776A66178299FF95A46C623DBC260F997E58FD514853DD40'
$coreVersion = '3.3.11'
$avrCoreVersion = '1.8.8'
$esp32Index = 'https://espressif.github.io/arduino-esp32/package_esp32_index.json'
$cliDirectory = Join-Path $projectRoot 'tools\arduino-cli'
$cli = Join-Path $cliDirectory 'arduino-cli.exe'
$downloads = Join-Path $projectRoot 'artifacts\downloads'
$archive = Join-Path $downloads "arduino-cli_$($cliVersion)_Windows_64bit.zip"

New-Item -ItemType Directory -Force -Path $cliDirectory, $downloads | Out-Null

$cliIsCurrent = $false
if (Test-Path -LiteralPath $cli -PathType Leaf) {
    $cliIsCurrent = (& $cli version 2>$null) -match "Version: $([regex]::Escape($cliVersion))"
}
if (-not $cliIsCurrent) {
    $url = "https://downloads.arduino.cc/arduino-cli/arduino-cli_$($cliVersion)_Windows_64bit.zip"
    Invoke-WebRequest -Uri $url -OutFile $archive
    $actualHash = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash
    if ($actualHash -ne $cliSha256) {
        throw "Arduino CLI checksum mismatch: expected $cliSha256, got $actualHash"
    }
    Expand-Archive -LiteralPath $archive -DestinationPath $cliDirectory -Force
}

$installedCore = & $cli core list --format json | ConvertFrom-Json
$esp32 = $installedCore.platforms | Where-Object id -eq 'esp32:esp32'
if ($esp32.installed_version -ne $coreVersion) {
    & $cli core update-index --additional-urls $esp32Index
    if ($LASTEXITCODE -ne 0) { throw 'Could not update the Arduino core index.' }
    & $cli core install "esp32:esp32@$coreVersion" --additional-urls $esp32Index
    if ($LASTEXITCODE -ne 0) { throw "Could not install ESP32 Core $coreVersion." }
}

$installedCore = & $cli core list --format json | ConvertFrom-Json
$avr = $installedCore.platforms | Where-Object id -eq 'arduino:avr'
if ($avr.installed_version -ne $avrCoreVersion) {
    & $cli core update-index
    if ($LASTEXITCODE -ne 0) { throw 'Could not update the Arduino core index.' }
    & $cli core install "arduino:avr@$avrCoreVersion"
    if ($LASTEXITCODE -ne 0) { throw "Could not install Arduino AVR Core $avrCoreVersion." }
}

Write-Output "Arduino CLI $cliVersion, ESP32 Core $coreVersion and Arduino AVR Core $avrCoreVersion are ready."
