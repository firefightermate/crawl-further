# Building

The repo builds three assemblies, all for the game's own Mono (.NET 3.5 profile, C# 7.3):

| Output | Source | What it is |
| --- | --- | --- |
| `CrawlFurther.Core.dll` | `src/CrawlFurther.Core` | The library. BepInEx plugin "Crawl Further Core", GUID `com.firefightermate.crawlfurther.core` |
| `CrawlFurther.dll` | `src/CrawlFurther` | The content mod, built on Core. GUID `com.firefightermate.crawlfurther` (configs and saves key on it, so it keeps its old name) |
| `ExampleGod.dll` | `examples/ExampleGod` | The sample mod the docs quote ([getting-started.md](getting-started.md)) |

## The game's DLLs

The code compiles against the game's and BepInEx's assemblies, which are not in the repo (they belong to their
owners). Copy them from an install of Crawl with BepInEx 5:

| From | Files |
| --- | --- |
| `Crawl/Crawl_Data/Managed` | `mscorlib.dll`, `System.dll`, `System.Core.dll`, `UnityEngine.dll`, `UnityEngine.UI.dll`, `Assembly-CSharp.dll`, `Assembly-CSharp-firstpass.dll`, `ex2D.Runtime.dll` |
| `Crawl/BepInEx/core` | `BepInEx.dll`, `0Harmony.dll` |

## With build.sh (bash)

Put the ten DLLs in `lib/` at the repo root and run:

```sh
./build.sh
```

It needs a .NET SDK (any recent one: it uses the SDK's `csc.dll` directly, with no restore and no NuGet). It finds
the newest SDK under `/usr/lib/dotnet`, `/usr/share/dotnet` or `~/.dotnet`. Set `CSC` to use another compiler,
and `OUT_DIR` to write somewhere other than `build/`:

```sh
CSC="dotnet /opt/dotnet/sdk/8.0.100/Roslyn/bincore/csc.dll" OUT_DIR=/tmp/out ./build.sh
```

Source files are passed in sorted order, so the assemblies list their types, and apply their Harmony patches, in
the same order on every machine. The build should finish with no warnings.

## With MSBuild or an IDE (Windows)

`CrawlFurther.sln` holds all three projects. `Directory.Build.props` sets the shared options and points the
references at your game install. Set `GameDir` there, or on the command line:

```sh
dotnet build CrawlFurther.sln -p:GameDir="D:\Games\Crawl"
```

The projects use the `Microsoft.NETFramework.ReferenceAssemblies` package so MSBuild can target .NET 3.5 without
the targeting pack. NuGet restores it on the first build. Both routes write to `build/`.

For a mod of your own outside this repo, copy the settings from `Directory.Build.props` into your project and add
a reference to `CrawlFurther.Core.dll` from `BepInEx/plugins/CrawlFurther`, with `Private` set to false so it is not
copied next to your DLL.

## Installing a development build

The game loads plugins from `BepInEx/plugins`. Core and Crawl: Further share one folder, and every sheet goes in
one flat `art` folder:

```
BepInEx/plugins/CrawlFurther/
  CrawlFurther.Core.dll
  CrawlFurther.dll
  art/        every .png and .json from art/core and art/out* (not the *_preview.png files)
  music/      the .ogg files from music/
```

`tools/package.sh` assembles exactly that (see below). A mod of your own goes in its own folder with its own
`art/`, like `BepInEx/plugins/ExampleGod`.

BepInEx writes its log to `BepInEx/LogOutput.log`. Core writes the self-test report to
`BepInEx/plugins/CrawlFurther/CrawlMod_selftest.txt` after the content packs register, and the banner at the top
left of the screen shows the problem count.

## Checks

Run these before a commit that touches content or art. Each prints OK or FAIL per check and exits 1 on a failure.

| Command | Checks |
| --- | --- |
| `python3 tools/validate.py` | Every sheet the C# names exists and has the animations and frames its code uses, sizes and feet, statues, shop art, portraits, vault text fitting its box, package contents, Harmony patch order and more. `-v` prints warnings and details |
| `python3 tools/check_trees.py` | Crawl: Further's evolution-tree rule and each monster's tip |
| `python3 tools/merge_tips.py` | Checks `data/tips/*.json` and regenerates `src/CrawlFurther/Tips/MonsterTipsGenerated.cs` |

They need Python 3 and Pillow. A few checks of `validate.py` compare against a dump of the game's own assets and
decompiled code (vanilla prefab names, clip frames, method overloads). Point `CRAWL_DUMP` at that folder (it holds
`db/`, `q/` and `src/`). Without it those checks are skipped with a warning. Missing `_preview.png` files (the rig
scripts make them, and they are not committed) are a warning too.

## Packaging

```sh
./build.sh
mkdir -p dist
tools/package.sh "$PWD/dist"       # dist/plugin_pkg.tar: CrawlFurther/ with both DLLs, art/, music/, README.txt
tools/thunderstore.sh "$PWD/dist"  # dist/Crawl_Further-thunderstore-<version>.zip
```

Give the output folder as an absolute path, and make it first.

`package.sh` runs `validate.py` first and stops if it fails (`SKIP_VALIDATE=1` overrides). It also writes a source
tarball next to the package. `thunderstore.sh` reads the version from `src/CrawlFurther/Plugin.cs` and builds the
Thunderstore zip (manifest, icon, `thunderstore/README.md`, `thunderstore/CHANGELOG.md`). If `dist/bepinex` holds
the BepInEx loader files, it also builds a manual-install zip with `thunderstore/INSTALL.txt`. Both scripts write
to `dist/` when no folder is given.

## Other tools

- `tools/music_convert.sh track.mp3 ...` converts tracks to the Ogg Vorbis that `ModMusic` loads, trims leading
  silence and normalises loudness. Needs ffmpeg with libvorbis.
- `tools/sprites/*.py` draw Crawl: Further's art ([art.md](art.md#the-rig-scripts)). They find the repo from their
  own path. Those that read the game dump use `CRAWL_DUMP`
  (default `build/dump`), and contact sheets and check boards go to `build/boards`.
- `examples/ExampleGod/tools/make_art.py` rebuilds the example's sheets from Crawl: Further's.
