# Crawl: Further

A content mod for Crawl, Powerhoof's local multiplayer dungeon game, and the modding library it is built on.

**Crawl: Further** adds nine gods with 189 monsters between them, 15 secret monsters, 25 weapons, 67 shop items,
32 room objects, hero origins, ghost forms and a vault page for every one of them, all with their own pixel art.
Everything from the mod carries a small violet gem in the menus. The full list is in [README.txt](README.txt) and
the changes per version in [thunderstore/CHANGELOG.md](thunderstore/CHANGELOG.md).

**Crawl Further Core** (`CrawlFurther.Core.dll`) is the library underneath. It has no content of its own. It lets a
BepInEx mod add gods, monsters with their own moves, shop items, weapons, room objects, vault pages, secrets, tips
and music, loads sprite sheets from PNG and JSON files, exports the game's own art, and keeps mods working with
Online Crawl and CrawlAPI. `examples/ExampleGod` is a small mod built on it.

## Install (players)

Crawl: Further runs on the Steam version of Crawl, with the BepInEx 5 mod loader.

- **With a mod manager** (r2modman, Thunderstore): install the package Crawl_Further. The loader comes with it.
- **By hand**: download `CrawlFurther-<version>.zip`, which includes the loader. In Steam, right-click Crawl >
  Manage > Browse local files, back up `Crawl.sav`, and unzip everything into that folder so `winhttp.dll` and the
  `BepInEx` folder sit next to `Crawl.exe`. On Steam Deck or Linux (Proton), set the launch options to
  `WINEDLLOVERRIDES="winhttp=n,b" %command%`.

When it loads, the top-left banner reads "Crawl: Further" with its version and "self-test OK". If it reports
problems, `BepInEx/plugins/CrawlFurther/CrawlMod_selftest.txt` says what failed; include that file and
`BepInEx/LogOutput.log` in a bug report. Updating from a version before 0.10.0: delete the old
`BepInEx/plugins/CrawlMod` folder first. Settings and saves carry over.

Settings live in `BepInEx/config`: `CrawlFurther.UI.cfg` (menus, music), `CrawlFurther.Objects.cfg` (how often room
objects appear) and `com.firefightermate.crawlfurther.cfg`.

## Make a mod (developers)

Start with [docs/getting-started.md](docs/getting-started.md), which walks through the example mod. Then:

| Page | Covers |
| --- | --- |
| [art.md](docs/art.md) | The sheet format, clips, `SpriteSheets`, `ClipBuilder`, exporting the game's atlases |
| [gods.md](docs/gods.md) | `GodDef`, evolution trees, perks, tips, statues |
| [monsters.md](docs/monsters.md) | `MonsterDef`, kits, effects, traits and behaviours, statuses |
| [items.md](docs/items.md) | Shop items and weapons |
| [objects.md](docs/objects.md) | Room objects and traps |
| [ui.md](docs/ui.md) | Vault pages, secrets, challenges, branding, tips, music, HUD timers |
| [events.md](docs/events.md) | Game events, and Harmony when you need it |
| [compat.md](docs/compat.md) | Online Crawl, CrawlAPI, other boss mods |
| [testing.md](docs/testing.md) | Test mode: the F2 panel and the game's debug menu |
| [building.md](docs/building.md) | Compiling, installing a development build, the checks, packaging |

A mod built on Core is a normal BepInEx plugin with `[BepInDependency("com.firefightermate.crawlfurther.core")]`. Core
currently ships inside the Crawl: Further package (`BepInEx/plugins/CrawlFurther/CrawlFurther.Core.dll`).

## Build

```sh
# copy the game's and BepInEx's DLLs into lib/ first (docs/building.md lists them)
./build.sh
```

This writes `build/CrawlFurther.Core.dll`, `build/CrawlFurther.dll` and `build/ExampleGod.dll`. On Windows, open
`CrawlFurther.sln` and set `GameDir` in `Directory.Build.props`.

## Repository

```
src/CrawlFurther.Core/   the library
src/CrawlFurther/        the content mod
examples/ExampleGod/     a small mod built on the library
art/core/                the library's own sheets
art/out*/                the content mod's sheets
data/tips/               monster tips and pause pages (merged into C# by tools/merge_tips.py)
music/                   the content mod's soundtrack
tools/                   checks, packaging, and the scripts that draw the art (tools/sprites)
thunderstore/            package text, icon and player changelog
docs/                    developer documentation
```

[CONTRIBUTING.md](CONTRIBUTING.md) has the code style and what to run before a pull request.
[CHANGELOG.md](CHANGELOG.md) tracks changes to the library and the repo.

## License

[MIT](LICENSE). Crawl, its art and its code belong to Powerhoof. The game's DLLs are never committed here.
