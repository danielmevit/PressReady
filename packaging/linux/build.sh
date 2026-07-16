#!/usr/bin/env bash
# Linux build: PyInstaller bundle -> portable tar.gz.
#
# Must run on Linux — PyInstaller cannot cross-compile. Produces a self-contained
# folder that works on any glibc distro without installing Python or Qt.
#
# NOTE: nothing here may be named a case-variant of "Laydown". This script gets
# run from WSL against /mnt/d, which is case-insensitive: a launcher called
# `laydown` silently *overwrote* the `Laydown` binary and then exec'd itself
# forever. It cost an afternoon, and CI would never have caught it — GitHub's ext4
# runners are case-sensitive, so there the two coexist and everything looks fine.
set -euo pipefail

cd "$(dirname "$0")/../.."
PY="${PYTHON:-python3}"
VERSION="$($PY -c 'import laydown; print(laydown.__version__)')"
NAME="Laydown-${VERSION}-linux-x86_64"

echo "=== Laydown ${VERSION} — Linux build ==="

rm -rf build dist
$PY -m PyInstaller Laydown.spec --noconfirm --distpath dist --workpath build

STAGE="dist/${NAME}"
mv dist/Laydown "${STAGE}"
chmod +x "${STAGE}/Laydown"

# Guard the case-collision class of bug: if anything replaced the binary with a
# script, or PyInstaller produced nothing useful, stop here rather than ship it.
BIN_SIZE=$(stat -c %s "${STAGE}/Laydown")
if [ "${BIN_SIZE}" -lt 1000000 ]; then
    echo "ERROR: dist binary is only ${BIN_SIZE} bytes — expected a multi-MB executable." >&2
    echo "       Something overwrote it (case-insensitive filesystem?)." >&2
    exit 1
fi

cat > "${STAGE}/Laydown.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Laydown
GenericName=PDF Imposition
Comment=Lay PDF pages out on press sheets
Exec=Laydown %f
Icon=laydown
Terminal=false
Categories=Graphics;Publishing;
MimeType=application/pdf;
DESKTOP

cp assets/icons/icon_256x256.png "${STAGE}/laydown-icon.png"
cp README.md LICENSE NOTICE "${STAGE}/" 2>/dev/null || true

cat > "${STAGE}/INSTALL.txt" <<'TXT'
Laydown — portable Linux build

Run it:
    ./Laydown

Add it to your applications menu (optional):
    cp Laydown.desktop  ~/.local/share/applications/
    cp laydown-icon.png ~/.local/share/icons/laydown.png
    sed -i "s|Exec=Laydown|Exec=$PWD/Laydown|" ~/.local/share/applications/Laydown.desktop

Needs a desktop session (X11 or Wayland). No Python or Qt installation required.
Check it works without a display:
    ./Laydown --smoke
TXT

tar -czf "dist/${NAME}.tar.gz" -C dist "${NAME}"
echo "=== built dist/${NAME}.tar.gz ($(du -h "dist/${NAME}.tar.gz" | cut -f1)) ==="
echo "    binary: $(du -h "${STAGE}/Laydown" | cut -f1)"
