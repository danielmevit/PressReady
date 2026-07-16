<#
    Windows build: PyInstaller bundle -> portable ZIP (+ MSIX where possible).

    KEEP THIS FILE PURE ASCII. Windows PowerShell 5.1 reads a BOM-less .ps1 as ANSI
    (cp1252), so a UTF-8 em-dash arrives as three bytes whose last one is a curly
    quote -- which PowerShell honours as a string terminator. One em-dash in a
    Write-Host message silently unbalanced every brace after it and the whole script
    failed to parse. tests/test_packaging.py enforces this.

    Handles both architectures. The arch is whatever the running Python is: a 32-bit
    Python produces a 32-bit build, so CI just points this at the right interpreter.

    MSIX is 64-bit only here -- it needs the Windows SDK's makeappx/signtool, and the
    32-bit audience is people on old machines who want a folder they can copy, not a
    packaged installer.

    Usage:
        powershell -ExecutionPolicy Bypass -File packaging\windows\build.ps1
        ... -SkipMsix        portable ZIP only
        ... -SkipPyInstaller reuse an existing dist\Laydown
#>
param(
    [switch]$SkipPyInstaller,
    [switch]$SkipMsix
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path "$PSScriptRoot\..\..").Path
Push-Location $root

# -- version + arch: both discovered, never restated --
$python = if ($env:PYTHON) { $env:PYTHON } else { "python" }
$version = (& $python -c "import laydown; print(laydown.__version__)").Trim()
$bits = (& $python -c "import struct; print(struct.calcsize('P') * 8)").Trim()
$arch = if ($bits -eq "32") { "x86" } else { "x64" }
$appVersion = "$version.0"   # MSIX wants four parts

if ($version -notmatch '^\d+\.\d+\.\d+$') {
    Write-Error "laydown/__init__.py must carry a three-part version (got '$version'); MSIX appends the fourth."
}

Write-Host "=== Laydown $version -- Windows $arch build ===" -ForegroundColor Cyan

$outDir = "$root\dist"
$stageDir = "$root\build\msix_stage"
$portableName = "Laydown-$version-windows-$arch-portable"

# -- 1. PyInstaller -----------------------------------
if (-not $SkipPyInstaller) {
    Write-Host "`n--- PyInstaller ---" -ForegroundColor Cyan
    & $python -m PyInstaller Laydown.spec --noconfirm --distpath dist --workpath build
    if ($LASTEXITCODE -ne 0) { Write-Error "PyInstaller failed" }
}
if (-not (Test-Path "$outDir\Laydown\Laydown.exe")) {
    Write-Error "No bundle at dist\Laydown -- run without -SkipPyInstaller"
}

# -- 2. Portable ZIP ----------------------------------
Write-Host "`n--- Portable ZIP ---" -ForegroundColor Cyan
$portableDir = "$outDir\$portableName"
if (Test-Path $portableDir) { Remove-Item $portableDir -Recurse -Force }
Copy-Item "$outDir\Laydown" $portableDir -Recurse
foreach ($doc in @("README.md", "LICENSE", "NOTICE")) {
    if (Test-Path "$root\$doc") { Copy-Item "$root\$doc" $portableDir }
}
@"
Laydown $version -- portable ($arch)

Run Laydown.exe. Nothing is installed and nothing is written outside this
folder except your own settings (in the registry under HKCU\Software\Laydown)
and any PDFs you export.

Windows may warn that the publisher is unknown: the binaries are unsigned.
More info -> Run anyway.
"@ | Set-Content "$portableDir\README-portable.txt" -Encoding UTF8

$zipPath = "$outDir\$portableName.zip"
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Compress-Archive -Path "$portableDir\*" -DestinationPath $zipPath
Write-Host "[ok] $zipPath" -ForegroundColor Green

# -- 3. MSIX (64-bit only) ----------------------------
if ($SkipMsix -or $arch -eq "x86") {
    Write-Host "`n[skip] MSIX (32-bit builds ship portable only)" -ForegroundColor Yellow
    Pop-Location
    exit 0
}

$sdk = Get-ChildItem "${env:ProgramFiles(x86)}\Windows Kits\10\bin" -Directory -ErrorAction SilentlyContinue |
    Where-Object { Test-Path "$($_.FullName)\x64\makeappx.exe" } |
    Sort-Object Name -Descending | Select-Object -First 1
if (-not $sdk) {
    Write-Host "[skip] MSIX -- no Windows 10 SDK found (portable ZIP is built)" -ForegroundColor Yellow
    Pop-Location
    exit 0
}
$makeappx = "$($sdk.FullName)\x64\makeappx.exe"
$signtool = "$($sdk.FullName)\x64\signtool.exe"
Write-Host "`n--- MSIX (SDK $($sdk.Name)) ---" -ForegroundColor Cyan

if (Test-Path $stageDir) { Remove-Item $stageDir -Recurse -Force }
New-Item -ItemType Directory -Path $stageDir | Out-Null
Copy-Item "$outDir\Laydown\*" $stageDir -Recurse

# Stamp the version into the staged manifest. It used to be copied verbatim, so the
# MSIX took whatever the checked-in manifest said and bumping the build did nothing.
$manifest = Get-Content "$root\AppxManifest.xml" -Raw
$manifest = [regex]::Replace($manifest, '(<Identity[^>]*?\sVersion=")[^"]+(")', "`${1}$appVersion`${2}")
if ($manifest -notmatch [regex]::Escape($appVersion)) {
    Write-Error "Could not stamp version $appVersion into AppxManifest.xml"
}
Set-Content "$stageDir\AppxManifest.xml" $manifest -Encoding UTF8

New-Item -ItemType Directory -Path "$stageDir\assets\icons\msix" -Force | Out-Null
Copy-Item "$root\assets\icons\msix\*" "$stageDir\assets\icons\msix\"

# The signing certificate. Users must trust the SAME certificate across releases, so
# CI restores a stable PFX from a repo secret (LAYDOWN_CERT_PFX_B64) before this
# script runs; the password rides in LAYDOWN_CERT_PASSWORD. A per-run throwaway
# cert is what shipped v0.3.0's first MSIX -- the .cer users needed to trust existed
# only on a dead runner VM, so Windows refused the install with 0x800B010A.
$certDir = "$root\certs"
$pfxPath = "$certDir\Laydown.pfx"
$cerPath = "$certDir\Laydown.cer"
$pfxPassword = if ($env:LAYDOWN_CERT_PASSWORD) { $env:LAYDOWN_CERT_PASSWORD } else { "Laydown2026" }
if (-not (Test-Path $pfxPath)) {
    Write-Host "Creating a self-signed certificate (first run, local builds only)" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $certDir -Force | Out-Null
    $cert = New-SelfSignedCertificate -Type Custom -Subject "CN=LaydownTeam" `
        -KeyUsage DigitalSignature -FriendlyName "Laydown" -CertStoreLocation "Cert:\CurrentUser\My" `
        -NotAfter (Get-Date).AddYears(5) `
        -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3", "2.5.29.19={text}")
    $pw = ConvertTo-SecureString -String $pfxPassword -Force -AsPlainText
    Export-PfxCertificate -Cert "Cert:\CurrentUser\My\$($cert.Thumbprint)" -FilePath $pfxPath -Password $pw | Out-Null
    Export-Certificate -Cert "Cert:\CurrentUser\My\$($cert.Thumbprint)" -FilePath $cerPath | Out-Null
}
if (-not (Test-Path $cerPath)) {
    # PFX came from the CI secret; derive the public half for publishing.
    $pw = ConvertTo-SecureString -String $pfxPassword -Force -AsPlainText
    $pfxData = Get-PfxData -FilePath $pfxPath -Password $pw
    Export-Certificate -Cert $pfxData.EndEntityCertificates[0] -FilePath $cerPath | Out-Null
}

$msixPath = "$outDir\Laydown-$version-windows-x64.msix"
if (Test-Path $msixPath) { Remove-Item $msixPath -Force }
& $makeappx pack /d $stageDir /p $msixPath /o
if ($LASTEXITCODE -ne 0) { Write-Error "makeappx failed" }
& $signtool sign /fd SHA256 /a /f $pfxPath /p $pfxPassword $msixPath
if ($LASTEXITCODE -ne 0) { Write-Error "signtool failed" }

# Ship the public certificate beside the installer: trusting it once is the install
# prerequisite, so it belongs on the release page, not in a doc nobody finds.
Copy-Item $cerPath "$outDir\Laydown-msix-signing.cer"

Write-Host "[ok] $msixPath" -ForegroundColor Green
Write-Host "[ok] $outDir\Laydown-msix-signing.cer (users trust this once)" -ForegroundColor Green
Write-Host "`nTrust the certificate once (elevated):" -ForegroundColor Yellow
Write-Host "  Import-Certificate -FilePath `"$cerPath`" -CertStoreLocation Cert:\LocalMachine\TrustedPeople"
Pop-Location
