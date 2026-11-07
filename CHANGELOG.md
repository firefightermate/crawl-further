# Changelog

Changes to Crawl Further Core and to the repository. What changed in the game for players is in
[thunderstore/CHANGELOG.md](thunderstore/CHANGELOG.md).

## 1.0.1

### Library (CrawlFurther.Core)
- `ModMark` places every violet mod gem, one owner per entry: no entry shows two (the vault cell and its big
  picture, the shop pedestal and its popup, a list pip and the portrait). `ModGem.Attach` and `AttachAt` are internal.
- `ModMark.MarkArt` marks art composed at run time; custom hero portraits no longer have the gem painted in.
- `CrawlFurther.UI.cfg` `ModGem = false` hides the gems.
- `tools/validate.py` checks the marks: one call site per context and no gem painted into art.
- The evolve panel's cost and wrath numbers copy their labels' font and material, so a font-swapping translation mod no longer breaks them. Slot-god art that can't be drawn is skipped and logged once.
- Patches that fail to apply are listed in the self-test report.
- `tools/package.sh` builds the source archive with `git archive`, so only committed files go in.

## 1.0.0

### Library (CrawlFurther.Core)
- The mod is split into two assemblies: `CrawlFurther.Core.dll`, a library with no content of its own, and
  `CrawlFurther.dll`, the content mod built on it. Both install to `BepInEx/plugins/CrawlFurther`. The content mod
  keeps its GUID, so configs and saves carry over.
- Public API for mods: `Further.AddMod` and `Further.AddPack`, `GameEvents` and `MonsterEvents`, `GodDef` and
  `DeityFactory`, `MonsterDef`, `Kit`, `FxKit` and `Strike`, `ItemDef` and `WeaponDef`, `ObjectDef`, vault
  categories and pages, secrets and challenges, branding, `ModMusic`, `HudTimers`.
- `Sheet` is renamed `SpriteSheet` and `ArtBank` is renamed `SpriteSheets`.
- `Ex2DExport` writes any loaded atlas or clip to PNG and JSON (F8 with `DebugKeys` on).
- The god select shows the god list as a grid that pages once it is full.
- Works alongside CrawlAPI and boss mods such as CrawlCustomBosses.
- Test mode: an F2 panel for trying gods, monsters and items without a full run, which mods can add pages to.
- A mod whose start callback throws is reported by the self-test.
- Monsters copied from a thief no longer steal the hero's gold unless their traits say so.

### Repository
- `examples/ExampleGod`, a small mod with one god, three monsters and a spell, built by `build.sh`.
- Developer docs in `docs/`, this changelog, `CONTRIBUTING.md` and `LICENSE`.
- Crawl: Further's self-test checks only its own gods' trees, so another mod's god no longer shows as a problem.
- `build.sh` finds the .NET SDK itself (`CSC` overrides it). The tools find the repo from their own path and the
  game dump from `CRAWL_DUMP`, and `validate.py` passes on a fresh clone without previews or the dump.
