#!/usr/bin/env bash
# Linux build: PyInstaller bundle -> portable tar.gz.
#
# Must run on Linux — PyInstaller cannot cross-compile. Produces a self-contained
# folder that works on any glibc distro without installing Python or Qt.
#
# NOTE: nothing here may be named a case-variant of "PressReady". This script gets
# run from WSL against /mnt/d, which is case-insensitive: a launcher called
# `pressready` silently *overwrote* the `PressReady` binary and then exec'd itself
# forever. It cost an afternoon, and CI would never have caught it — GitHub's ext4
# runners are case-sensitive, so there the two coexist and everything looks fine.
set -euo pipefail

cd "$(dirname "$0")/../.."
PY="${PYTHON:-python3}"
VERSION="$($PY -c 'import pressready; print(pressready.__version__)')"
NAME="PressReady-${VERSION}-linux-x86_64"

echo "=== PressReady ${VERSION} — Linux build ==="

rm -rf build dist
$PY -m PyInstaller PressReady.spec --noconfirm --distpath dist --workpath build

STAGE="dist/${NAME}"
mv dist/PressReady "${STAGE}"
chmod +x "${STAGE}/PressReady"

# Guard the case-collision class of bug: if anything replaced the binary with a
# script, or PyInstaller produced nothing useful, stop here rather than ship it.
BIN_SIZE=$(stat -c %s "${STAGE}/PressReady")
if [ "${BIN_SIZE}" -lt 1000000 ]; then
    echo "ERROR: dist binary is only ${BIN_SIZE} bytes — expected a multi-MB executable." >&2
    echo "       Something overwrote it (case-insensitive filesystem?)." >&2
    exit 1
fi

cat > "${STAGE}/PressReady.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=PressReady
GenericName=PDF Imposition
Comment=Lay PDF pages out on press sheets
Exec=PressReady %f
Icon=pressready
Terminal=false
Categories=Graphics;Publishing;
MimeType=application/pdf;
DESKTOP

cp assets/icons/icon_256x256.png "${STAGE}/pressready-icon.png"
cp README.md LICENSE NOTICE "${STAGE}/" 2>/dev/null || true

cat > "${STAGE}/INSTALL.txt" <<'TXT'
PressReady — portable Linux build

Run it:
    ./PressReady

Add it to your applications menu (optional):
    cp PressReady.desktop  ~/.local/share/applications/
    cp pressready-icon.png ~/.local/share/icons/pressready.png
    sed -i "s|Exec=PressReady|Exec=$PWD/PressReady|" ~/.local/share/applications/PressReady.desktop

Needs a desktop session (X11 or Wayland). No Python or Qt installation required.
Check it works without a display:
    ./PressReady --smoke
TXT

tar -czf "dist/${NAME}.tar.gz" -C dist "${NAME}"
echo "=== built dist/${NAME}.tar.gz ($(du -h "dist/${NAME}.tar.gz" | cut -f1)) ==="
echo "    binary: $(du -h "${STAGE}/PressReady" | cut -f1)"
