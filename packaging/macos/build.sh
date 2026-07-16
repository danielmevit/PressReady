#!/usr/bin/env bash
# macOS build: PyInstaller .app -> .dmg.
#
# Must run on macOS. The .icns is generated here from the PNGs rather than checked
# in, so the icon can never drift from the one the app uses.
set -euo pipefail

cd "$(dirname "$0")/../.."
PY="${PYTHON:-python3}"
VERSION="$($PY -c 'import laydown; print(laydown.__version__)')"
ARCH="$(uname -m)"
NAME="Laydown-${VERSION}-macos-${ARCH}"

echo "=== Laydown ${VERSION} — macOS build (${ARCH}) ==="

# --- icon: PNGs -> .icns
ICONSET="build/laydown.iconset"
rm -rf "${ICONSET}"; mkdir -p "${ICONSET}"
for size in 16 32 128 256; do
  cp "assets/icons/icon_${size}x${size}.png" "${ICONSET}/icon_${size}x${size}.png"
  double=$((size * 2))
  if [ -f "assets/icons/icon_${double}x${double}.png" ]; then
    cp "assets/icons/icon_${double}x${double}.png" "${ICONSET}/icon_${size}x${size}@2x.png"
  fi
done
cp assets/icons/icon_512x512.png "${ICONSET}/icon_512x512.png" 2>/dev/null || \
  cp assets/icons/icon_1024x1024.png "${ICONSET}/icon_512x512.png"
cp assets/icons/icon_1024x1024.png "${ICONSET}/icon_512x512@2x.png"
iconutil -c icns "${ICONSET}" -o assets/icons/laydown.icns
echo "[ok] built assets/icons/laydown.icns"

rm -rf build/Laydown dist
$PY -m PyInstaller Laydown.spec --noconfirm --distpath dist --workpath build

# --- dmg
STAGE="build/dmg"
rm -rf "${STAGE}"; mkdir -p "${STAGE}"
cp -R "dist/Laydown.app" "${STAGE}/"
ln -s /Applications "${STAGE}/Applications"
cp README.md LICENSE "${STAGE}/" 2>/dev/null || true

hdiutil create -volname "Laydown ${VERSION}" -srcfolder "${STAGE}" \
  -ov -format UDZO "dist/${NAME}.dmg"

echo "=== built dist/${NAME}.dmg ==="
echo "NOTE: unsigned. First launch is right-click -> Open (Gatekeeper)."
