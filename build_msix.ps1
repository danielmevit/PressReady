# build_msix.ps1 — Build PressReady MSIX installer from scratch
# Usage:  powershell -ExecutionPolicy Bypass -File build_msix.ps1
#
# Prerequisites:
#   - Python 3.10+ with PyQt6 and PyMuPDF installed
#   - PyInstaller          (pip install pyinstaller)
#   - Windows 10 SDK       (winget install Microsoft.WindowsSDK.10.0.26100)
#   - Self-signed cert     (created automatically on first run)

param(
    [switch]$SkipPyInstaller,
    [switch]$SkipSign
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Definition

# ── locate Windows SDK ───────────────────────────────
$sdkBase = "${env:ProgramFiles(x86)}\Windows Kits\10\bin"
if (-not (Test-Path $sdkBase)) {
    Write-Error "Windows 10 SDK not found. Install with:  winget install Microsoft.WindowsSDK.10.0.26100"
}
$sdkVer = Get-ChildItem -Path $sdkBase -Directory |
    Where-Object { $_.Name -match '^\d+\.\d+' } |
    Sort-Object Name -Descending |
    Select-Object -First 1
$sdk = "$($sdkVer.FullName)\x64"
$makeappx = "$sdk\makeappx.exe"
$signtool = "$sdk\signtool.exe"

foreach ($tool in @($makeappx, $signtool)) {
    if (-not (Test-Path $tool)) { Write-Error "Missing: $tool" }
}
Write-Host "[OK] SDK tools: $sdk" -ForegroundColor Green

# ── config ───────────────────────────────────────────
$appVersion  = "2.0.0.0"
$pfxPath     = "$root\certs\PressReady.pfx"
$pfxPassword = "PressReady2026"
$cerPath     = "$root\certs\PressReady.cer"
$stageDir    = "$root\msix_stage"
$outDir      = "$root\installer_output"
$msixPath    = "$outDir\PressReady_2.0.0.msix"

# ── Step 1: PyInstaller build ────────────────────────
if (-not $SkipPyInstaller) {
    Write-Host "`n=== Step 1/5: PyInstaller build ===" -ForegroundColor Cyan
    Push-Location $root
    python -m PyInstaller PressReady.spec --noconfirm
    if ($LASTEXITCODE -ne 0) { Write-Error "PyInstaller failed" }
    Pop-Location
    Write-Host "[OK] PyInstaller build complete" -ForegroundColor Green
} else {
    Write-Host "`n=== Step 1/5: PyInstaller build (skipped) ===" -ForegroundColor Yellow
}

# ── Step 2: create signing certificate (if missing) ──
Write-Host "`n=== Step 2/5: Signing certificate ===" -ForegroundColor Cyan
if (-not (Test-Path $pfxPath)) {
    Write-Host "Creating self-signed certificate..."
    New-Item -ItemType Directory -Path "$root\certs" -Force | Out-Null

    $cert = New-SelfSignedCertificate `
        -Type Custom `
        -Subject "CN=PressReadyTeam" `
        -KeyUsage DigitalSignature `
        -FriendlyName "PressReady Code Signing" `
        -CertStoreLocation "Cert:\CurrentUser\My" `
        -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3","2.5.29.19={text}") `
        -NotAfter (Get-Date).AddYears(5)

    $pwd = ConvertTo-SecureString -String $pfxPassword -Force -AsPlainText
    Export-PfxCertificate -Cert $cert -FilePath $pfxPath -Password $pwd | Out-Null
    Export-Certificate -Cert $cert -FilePath $cerPath | Out-Null
    Write-Host "[OK] Certificate created: $pfxPath" -ForegroundColor Green
    Write-Host ""
    Write-Host "IMPORTANT: To install the MSIX, the cert must be trusted." -ForegroundColor Yellow
    Write-Host "Run this ONCE as Administrator:" -ForegroundColor Yellow
    Write-Host "  Import-Certificate -FilePath `"$cerPath`" -CertStoreLocation Cert:\LocalMachine\TrustedPeople" -ForegroundColor White
} else {
    Write-Host "[OK] Certificate already exists: $pfxPath" -ForegroundColor Green
}

# ── Step 3: stage MSIX contents ──────────────────────
Write-Host "`n=== Step 3/5: Stage MSIX package ===" -ForegroundColor Cyan
if (Test-Path $stageDir) { Remove-Item -Recurse -Force $stageDir }
New-Item -ItemType Directory -Path $stageDir | Out-Null

Copy-Item "$root\dist\PressReady\PressReady.exe" "$stageDir\"
Copy-Item "$root\dist\PressReady\_internal" "$stageDir\_internal" -Recurse
Copy-Item "$root\AppxManifest.xml" "$stageDir\"
New-Item -ItemType Directory -Path "$stageDir\assets\icons\msix" -Force | Out-Null
Copy-Item "$root\assets\icons\msix\*" "$stageDir\assets\icons\msix\"

Write-Host "[OK] Staging complete" -ForegroundColor Green

# ── Step 4: package and sign MSIX ────────────────────
Write-Host "`n=== Step 4/5: Package and sign MSIX ===" -ForegroundColor Cyan
New-Item -ItemType Directory -Path $outDir -Force | Out-Null
if (Test-Path $msixPath) { Remove-Item $msixPath }

& $makeappx pack /d "$stageDir" /p "$msixPath" /o | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Error "makeappx failed" }
Write-Host "[OK] MSIX packaged" -ForegroundColor Green

if (-not $SkipSign) {
    & $signtool sign /fd SHA256 /a /f "$pfxPath" /p $pfxPassword "$msixPath" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Error "signtool failed" }
    Write-Host "[OK] MSIX signed" -ForegroundColor Green
} else {
    Write-Host "[SKIP] Signing skipped" -ForegroundColor Yellow
}

# ── Step 5: portable ZIP ─────────────────────────────
Write-Host "`n=== Step 5/5: Portable ZIP ===" -ForegroundColor Cyan
$zipPath = "$outDir\PressReady_2.0.0-windows-x64.zip"
if (Test-Path $zipPath) { Remove-Item $zipPath }

$distDir = "$root\dist\PressReady"
Compress-Archive -Path "$distDir\*" -DestinationPath $zipPath -Force
$zipSize = [math]::Round((Get-Item $zipPath).Length / 1MB, 1)
Write-Host "[OK] Portable ZIP: $zipPath ($zipSize MB)" -ForegroundColor Green

# ── cleanup staging ──────────────────────────────────
Remove-Item -Recurse -Force $stageDir

# ── done ─────────────────────────────────────────────
$msixSize = [math]::Round((Get-Item $msixPath).Length / 1MB, 1)
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  BUILD COMPLETE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  MSIX installer:  $msixPath ($msixSize MB)" -ForegroundColor White
Write-Host "  Portable ZIP:   $zipPath ($zipSize MB)" -ForegroundColor White
Write-Host ""
Write-Host "MSIX — double-click to install, or:" -ForegroundColor Yellow
Write-Host "  Add-AppxPackage -Path `"$msixPath`"" -ForegroundColor Gray
Write-Host ""
Write-Host "ZIP (portable) — extract anywhere and run PressReady.exe" -ForegroundColor Yellow
Write-Host ""
