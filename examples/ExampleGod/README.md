# Example God

A small mod built only on Crawl Further Core. It adds Glimmer, a god with three starting monsters, and a shop spell.
[docs/getting-started.md](../../docs/getting-started.md) walks through it.

| File | What it shows |
| --- | --- |
| `ExampleGodPlugin.cs` | The BepInEx plugin: register with Core in `Awake`, set up and queue the content pack once the game has booted |
| `GlimmerPack.cs` | The god (`GodDef`), its three monsters (`MonsterDef`) and their kits, tips, pause page and vault lines |
| `GlimmerFx.cs` | Effect templates: melee hitboxes, two projectiles and the god's perk |
| `GlimmerGlow.cs` | A `MonsterBehaviour` that receives a clip event |
| `GlimmerItems.cs` | A shop spell copied from a vanilla one (`ItemDef`) |
| `GlimmerEvents.cs` | `GameEvents` instead of Harmony patches |
| `GlimmerTests.cs` | A page in the test panel (F2, with test mode on) |
| `art/` | The sheets, recoloured from Crawl: Further's by `tools/make_art.py` |

## Build

From the repo root, `./build.sh` writes `build/ExampleGod.dll`. Or build `ExampleGod.csproj`, which takes its
settings from the repo's `Directory.Build.props` ([docs/building.md](../../docs/building.md)).

## Install

```
BepInEx/plugins/ExampleGod/
  ExampleGod.dll
  art/        the .png and .json files from this folder's art/
```

Crawl: Further must be installed too: it carries `CrawlFurther.Core.dll`.

## Make it yours

Change the GUID in `ExampleGodPlugin.cs` and the ids: every sheet, monster, item and clip name must be unique across
all installed mods.
