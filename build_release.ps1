$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name MemoSticker `
    MemoSticker.pyw

$hash = (Get-FileHash -Algorithm SHA256 -LiteralPath ".\dist\MemoSticker.exe").Hash.ToLowerInvariant()
Set-Content -LiteralPath ".\dist\MemoSticker.exe.sha256" -Value "$hash  MemoSticker.exe" -Encoding ascii
Write-Host "Built dist\MemoSticker.exe"
Write-Host "SHA-256: $hash"
