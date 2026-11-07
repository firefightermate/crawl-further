#!/bin/bash
# Assemble the plugin folder BepInEx/plugins/CrawlFurther (both DLLs, every art sheet, music, README) and tar it for the
# PC (plugin_pkg.tar holds CrawlFurther/...).
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)
OUT=${1:-$ROOT/dist}
mkdir -p "$OUT"
BUILD=${OUT_DIR:-$ROOT/build}
# every sheet the code loads must exist and pass the art checks (set SKIP_VALIDATE=1 to package anyway)
if [ -z "$SKIP_VALIDATE" ]; then
  python3 -W ignore "$ROOT/tools/validate.py" || { echo "validate.py failed: not packaging (SKIP_VALIDATE=1 to override)"; exit 1; }
fi
for dll in CrawlFurther.Core.dll CrawlFurther.dll; do
  [ -f "$BUILD/$dll" ] || { echo "$BUILD/$dll missing: run ./build.sh first"; exit 1; }
done
NEWER=$(find "$ROOT/src" -name '*.cs' -newer "$BUILD/CrawlFurther.dll" | head -3)
[ -n "$NEWER" ] && echo "WARNING: $BUILD/CrawlFurther.dll is older than $NEWER ... (run ./build.sh first)"
STAGE=$(mktemp -d)/CrawlFurther
mkdir -p "$STAGE/art"
# Core's own sheets (art/core) and the content mod's (art/out*) all go into the one flat art folder SpriteSheets reads
for d in "$ROOT"/art/core "$ROOT"/art/out*; do
  for f in "$d"/*.json; do
    [ -e "$f" ] || continue
    b=$(basename "$f" .json)
    case $b in *_preview|board|contact_idle|fx_all|designs_board) continue;; esac
    [ -f "$d/$b.png" ] && cp "$d/$b.png" "$d/$b.json" "$STAGE/art/"
  done
done
# Crawl: Further soundtrack (ModMusic loads every .ogg/.wav in plugins/CrawlFurther/music); placeholder test tones stay home
mkdir -p "$STAGE/music"
for f in "$ROOT"/music/*.ogg "$ROOT"/music/*.wav; do
  [ -e "$f" ] || continue
  case $(basename "$f") in placeholder*) continue;; esac
  cp "$f" "$STAGE/music/"
done
cp "$BUILD/CrawlFurther.Core.dll" "$BUILD/CrawlFurther.dll" "$ROOT/README.txt" "$STAGE/"
tar cf "$OUT/plugin_pkg.tar" -C "$(dirname "$STAGE")" CrawlFurther
(cd "$(dirname "$ROOT")" && tar czf "$OUT/CrawlMod-src.tar.gz" --exclude="$(basename "$ROOT")/build" --exclude='*/__pycache__' \
  --exclude="$(basename "$ROOT")/art/raw" "$(basename "$ROOT")")
echo "packaged $(ls "$STAGE/art" | wc -l) art files -> $OUT/plugin_pkg.tar"
