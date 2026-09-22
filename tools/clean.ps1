$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$generated = @(
    (Join-Path $projectRoot '.pytest_cache'),
    (Join-Path $projectRoot 'python\.pytest_cache'),
    (Join-Path $projectRoot 'python\build'),
    (Join-Path $projectRoot 'python\dist'),
    (Join-Path $projectRoot 'tools\arduino-cli'),
    (Join-Path $projectRoot 'artifacts\arduino-cli')
)

foreach ($path in $generated) {
    if (Test-Path -LiteralPath $path) {
        Remove-Item -LiteralPath $path -Recurse -Force
    }
}

Get-ChildItem -LiteralPath (Join-Path $projectRoot 'python') -Directory -Recurse -Force |
    Where-Object Name -eq '__pycache__' |
    Remove-Item -Recurse -Force

Write-Output 'Removed Python caches and bootstrapped Arduino CLI/config. artifacts/dist was preserved.'
