# Changelog

Changes to Crawl Further Core and to the repository. What changed in the game for players is in
[thunderstore/CHANGELOG.md](thunderstore/CHANGELOG.md).

## 1.2.0

### Library (CrawlFurther.Core)
- A mod monster's vault page without a challenge shows `LibraryEntries.NoChallengeText` ("No challenge
  available") where the challenge lines go, in the same text.

### Repository
- The origin picker's blob page copied the god list after the picker had switched that list off, so its
  MenuTextMenu never ran and took no input. Every copy of the god list is now switched on when it is made. The
  blob page logs `ModBlobList: ...` when it is built and `Blob step: open / confirm / back / locked blob` as it is
  used.
### Repository
- The blob choice is its own page of the origin picker, after the ghost form, instead of a row on the ghost page.
  It is a copy of the god list like the origin and form pages, one entry per blob laid over a row of starter
  boxes, with each entry's mouse hotspot set to its column. Every player's input reaches it the way it reaches
  the god list. The old row (`GhostBlobRow`) is gone.
- Text that could be cut or overlap now fits: monster tips are laid out from the drawn text (the OnGUI fallback
  stacked the title over a body taller than it allowed for), the god select's paragraphs keep to four lines
  (`PanelText`), long vault titles and the new-slot banner's lines shrink to fit, and the load banner and test panel
  wrap. `tools/validate.py` has a new `textfit` check for tips, god select texts, banner lines and pause subtitles.

### Library (CrawlFurther.Core)
- Mod monsters have the game's own vault challenge: its button, level, HUD, scoring and save, hooked in through
  their vault entries. A monster a player can become (reached from a god's starters, or a secret monster and its
  evolutions) gets the goal for its evolution cost from `Challenges.GoalByCost` (4, 5, 7, 10 at costs 0, 1, 2.5
  and 4: the game's own averages). Minions and ghost blobs get none. `MonsterDef.challenge` / `ChallengeDef` (or
  `Challenges.Register`) sets a goal or takes the challenge away. See [docs/ui.md](docs/ui.md#monster-challenges).
- A mod monster's vault page shows the game's challenge lines under its line, copied from the vault's live text,
  as many as fit above the buttons, best level first (`VaultGrid.ShowChallengePage`). The MONSTERS summary counts
  mod challenges passed. `tools/validate.py` (vaultfit) now keeps monster vault lines to three rows so at least one
  challenge line fits; 23 of Crawl: Further's lines were shortened. The challenge-passed tick is the game's own,
  so the gem of a MONSTERS cell moved to its bottom-left corner.
- No achievement is granted while a mod monster's challenge is played (`AchievementBase.Unlock` is skipped), and mod
  challenges still never count toward the game's challenge achievements.
- Test mode: Run > Monster challenge (from the menus) starts any monster's challenge (`TestGame.StartChallenge`);
  no challenge score is saved while test mode is on.
- Self-test: a "vault challenges" section (every built mod monster has its vault entry, found by prefab and by save
  key, with a goal exactly when it should), and Crawl: Further's "monster challenges" (189 god monsters and 15
  secret monsters have one, the ghost blobs none).

## 1.1.0

### Library (CrawlFurther.Core)
- `GhostBlobs` and `GhostBlobDef`: the blobs a ghost spawns with Back. Every form has the regular blob; a form can
  earn a blob of its own, which becomes its default, and other forms may be allowed to pick it. Picks are kept per
  player and per form. A blob can be locked behind a challenge, limited to some forms and cost more than one body of
  ectoplasm. See [docs/monsters.md](docs/monsters.md#ghost-blobs).
- `Silhouette` is public, for drawing a locked pick as a dark outline.

## 1.0.2

### Library (CrawlFurther.Core)
- `TierRules` holds the rules for evolved monsters. Their hits on the hero are no longer softened (they were 0.85x
  at tier 2 and 0.8x at tier 3), and their specials charge in 0.8x the time the kit sets instead of 1.25x.
- `MonsterDef.damageMult` scales one monster's hits on the hero. `specialChargeTime` and `attackCooldownMult` now
  apply after the kit, so a monster's balance numbers all sit on its def line.
- `MonsterFactory.Tier` gives each built monster's tier. Statue rooms and the self-test use it to find finals.
- `ModUtil.MonsterSource(body)` builds a body's own hits the way the game builds its attacks. It credits
  `Player.GetAttackSpawnerPlayer` (an AI body's hits credit the player who made it) and carries
  `Player.GetDamageModifierStack`, so a hit that a behaviour deals or spawns scales with god perks and runes. The
  hitting body stays the body. `ModMonster.OwnSource` and the gods' and secrets' own sources use it. Before, an AI
  body's hits credited nobody, and a hero killed by one was never replaced (`SystemLevel.CoroutineHeroDeath` gives
  up without a killer).
- `ModUtil.HandOn` passes a source and its modifiers on to a new effect; `FxFactory.SpawnOwned`, the echo spawners
  and Kaurn nodes use it.
- `HeroHandover`: a hero killed in an ordinary room by a hit that still credits nobody (another mod's, say) passes
  the crown to the player behind the body or effect that hit, and the log names the source.

## 1.0.1

### Library (CrawlFurther.Core)
- Online Crawl 0.4.1 and older: when a client comes back before the host timed its old session out (same Steam
  id, within 12 s), the host drops the old session first, so the new one starts clean instead of resuming a stale
  mirror state that left the returning player with an empty or broken screen. The self-test's online section says
  whether this is on.
- `PanelInput` lets go of a player whose holder was destroyed without freeing them, and `SlotEditorUI.End` always
  frees its player, so a player who left mid-edit and joined again is never locked out of their menus.
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
