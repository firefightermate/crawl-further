#!/bin/bash
# Build both Crawl: Further downloads from the packaged plugin (run tools/package.sh first):
#   Crawl_Further-thunderstore-<ver>.zip   manifest.json, icon.png, README.md, CHANGELOG.md, plugins/CrawlFurther/...
#   CrawlFurther-<ver>.zip                 the manual install: BepInEx loader (from $OUT/bepinex) + the plugin +
#                                          "INSTALL - READ ME FIRST.txt" (thunderstore/INSTALL.txt)
# The plugin folder is BepInEx/plugins/CrawlFurther (CrawlFurther.Core.dll + CrawlFurther.dll); the plugin GUID and
# config file names are unchanged, so updates keep settings and saves. The old plugins/CrawlMod folder must go
# (INSTALL.txt says so).
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)
OUT=${1:-$ROOT/dist}
VER=$(grep -o 'VERSION = "[0-9.]*"' "$ROOT/src/CrawlFurther/Plugin.cs" | grep -o '[0-9.]*')
TMP=$(mktemp -d)
mkdir -p "$TMP/plugins"
tar xf "$OUT/plugin_pkg.tar" -C "$TMP/plugins"      # -> plugins/CrawlFurther/{CrawlFurther.Core.dll,CrawlFurther.dll,README.txt,art/,music/}
cp "$ROOT/thunderstore/icon.png" "$ROOT/thunderstore/README.md" "$TMP/"
[ -f "$ROOT/thunderstore/CHANGELOG.md" ] && cp "$ROOT/thunderstore/CHANGELOG.md" "$TMP/"
cat > "$TMP/manifest.json" <<JSON
{
  "name": "Crawl_Further",
  "version_number": "$VER",
  "website_url": "https://github.com/firefightermate/crawl-further",
  "description": "9 new gods with 189 monsters, 15 secret monsters, 25 weapons, 67 shop items, 32 room objects, hero origins, ghost forms and a secrets vault, all with their own art. Works with Online Crawl. Includes the Crawl Further Core modding library.",
  "dependencies": ["Crawl_Modding-BepInExPack_Crawl-5.4.2305"]
}
JSON
python3 -c "import json;d=json.load(open('$TMP/manifest.json'));assert len(d['description'])<=250,len(d['description']);print('manifest ok',d['name'],d['version_number'],len(d['description']))"
ZIP="$OUT/Crawl_Further-thunderstore-$VER.zip"
rm -f "$ZIP"
(cd "$TMP" && python3 -c "
import zipfile,os
z=zipfile.ZipFile('$ZIP','w',zipfile.ZIP_DEFLATED)
for dp,dn,fn in os.walk('.'):
    for f in fn:
        p=os.path.join(dp,f)[2:]
        z.write(p,p)
z.close()")
echo "-> $ZIP"

# manual install zip (needs the BepInEx loader files in $OUT/bepinex)
if [ -d "$OUT/bepinex/BepInEx" ]; then
  M=$(mktemp -d)
  cp -r "$OUT/bepinex/." "$M/"
  rm -f "$M/changelog.txt"
  mkdir -p "$M/BepInEx/plugins" "$M/BepInEx/patchers"
  cp -r "$TMP/plugins/CrawlFurther" "$M/BepInEx/plugins/"
  sed "s/__VER__/$VER/g" "$ROOT/thunderstore/INSTALL.txt" > "$M/INSTALL - READ ME FIRST.txt"
  MZ="$OUT/CrawlFurther-$VER.zip"
  rm -f "$MZ"
  (cd "$M" && python3 -c "
import zipfile,os
z=zipfile.ZipFile('$MZ','w',zipfile.ZIP_DEFLATED)
for dp,dn,fn in os.walk('.'):
    for d in dn:
        p=os.path.join(dp,d)[2:]
        if not os.listdir(os.path.join(dp,d)): z.writestr(p+'/','')
    for f in fn:
        p=os.path.join(dp,f)[2:]
        z.write(p,p)
z.close()")
  echo "-> $MZ"
else
  echo "no $OUT/bepinex: skipped the manual install zip"
fi
