param(
    [string]$ConfigPath = "$env:APPDATA\codex-nock\config.toml"
)

$ErrorActionPreference = "Stop"

python -m pip install -e .
python -m codex_nock setup-desktop --config $ConfigPath

Write-Host ""
Write-Host "Next:"
Write-Host "1. Restart Codex."
Write-Host "2. Test the desktop popup:"
Write-Host "   python -m codex_nock test"
