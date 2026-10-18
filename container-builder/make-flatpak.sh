#!/usr/bin/env bash
# Pack the compiled FigCraft binaries into a standalone .flatpak bundle for SteamOS.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_ID="ai.storyteller.figcraft"
RUNTIME="org.freedesktop.Platform"
SDK="org.freedesktop.Sdk"
RUNTIME_VERSION="26.08"
DIST="$ROOT/dist-deck"
WORK="$HOME/.cache/figcraft-deck/flatpak-work"

mkdir -p "$DIST" "$WORK"
rm -rf "$WORK/build" "$WORK/repo" "$WORK/stage"
mkdir -p "$WORK/build" "$WORK/stage"

# Find tarball in dist-deck or dist
TARBALL="$(ls -t "$DIST"/figcraft-*-linux-x86_64.tar.gz 2>/dev/null | head -1 || true)"
if [ -z "$TARBALL" ]; then
  TARBALL="$(ls -t "$ROOT"/dist/release/figcraft-*-linux-x86_64.tar.gz 2>/dev/null | head -1 || true)"
fi
if [ -z "$TARBALL" ]; then
  echo "error: No tarball found in $DIST or $ROOT/dist/release. Run compilation and package first." >&2
  exit 1
fi

echo "==> Unpacking $(basename "$TARBALL")..."
tar -xzf "$TARBALL" -C "$WORK/stage" --strip-components=1

echo "==> Initializing Flatpak build directory..."
flatpak build-init "$WORK/build" "$APP_ID" "$SDK" "$RUNTIME" "$RUNTIME_VERSION"

echo "==> Installing files into sandbox..."
mkdir -p "$WORK/build/files/bin" "$WORK/build/files/share"
cp -a "$WORK/stage/bin/." "$WORK/build/files/bin/"
cp -a "$WORK/stage/share/." "$WORK/build/files/share/"

echo "==> Finishing Flatpak sandbox permissions..."
flatpak build-finish "$WORK/build" \
  --command=figcraft \
  --share=ipc \
  --share=network \
  --socket=wayland \
  --socket=fallback-x11 \
  --device=dri \
  --filesystem=home \
  --filesystem=xdg-pictures \
  --filesystem=xdg-documents \
  --filesystem=xdg-download

echo "==> Exporting to local OSTree repo..."
flatpak build-export "$WORK/repo" "$WORK/build" stable

OUT="$DIST/figcraft-deck.flatpak"
echo "==> Creating Flatpak bundle: $OUT..."
flatpak build-bundle "$WORK/repo" "$OUT" "$APP_ID" stable

echo "==> Flatpak bundle created successfully!"
ls -lh "$OUT"
echo
echo "==> Installing Flatpak locally on SteamOS..."
flatpak install --user --reinstall -y "$OUT"
echo "==> Testing figcraft-cli inside Flatpak sandbox..."
flatpak run --command=figcraft-cli "$APP_ID" --version
echo "==> Done!"
