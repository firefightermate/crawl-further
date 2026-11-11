# Changelog

Changes to Crawl Further Core and to the repository. What changed in the game for players is in
[thunderstore/CHANGELOG.md](thunderstore/CHANGELOG.md).

## 1.3.3

### Content
- Carrion Saint (`SaintFlock`): Murder looses `Flock` (5) crows one after another from its shoulders in a fan aimed at
  the hero; `CrowWall` lives 1.1 s and seeks (`OssCrowSeekFx.turn`, now a field: 70 for a sent crow, 45 for Murder).
- Jelly Siren (`JellyTrail`): the lash reaches `LashReach` (75 px), drawn as tentacles flung out and drawn back
  (`BelLashOut`), with the hitbox to match; Jet Pulse stretches the trail to `TrailSurge` (140 px) for `Surge` s, then
  it shrinks back.
- Slime Hag (`HagKnot`): a landed bite wraps the hero (new sheet `FxBelHagKnot`: Wrap, Hold, Tear), roots him, and
  tears for a second bite if he is still within 40 px.
- Finals: `TierRules.T3Health` and `T3Damage` 1.2 after playtests; `challenge_goals.py` divides the buff back out
  (`PLAYTEST`), so goals are unchanged.

### Repository
- `tools/concepts/chaos_biomes.py`: concept room mock-ups for the chaos biomes (not shipped).

## 1.3.2

### Content
- `ChallengeGoalsGenerated`: each mod monster's vault challenge goal, registered as its `ChallengeDef` unless its
  def sets one. `Challenges.GoalByCost` stays as the fallback.
- Tier numbers: starters' hits x1.62 (was 1.45), tier 2 health x1.14 and hits x1.13 (were 1.1 and 1.08). Each tier's
  median monster is about 1.08 of the game's own.

### Library (CrawlFurther.Core)
- Test mode: `[Testing] OpenEverything` in `CrawlMod.Debug.cfg` (on by default) opens everything from the start of
  the game, so menus built at boot show it. The test panel's switch saves to it.

### Repository
- `tools/challenge_goals.py` sets the goals: each monster's simulated score with the in-game tier numbers, half way
  from its tier's goal, inside the game's own range for the tier. Checked against the game's 59 monster challenges,
  the model gets each tier's average right but not the order within a tier, hence the half step.
- `tools/challenge_model/` (`modx.py`, `vanilla.py`, `power.py`): the monsters' combat numbers the model reads.

## 1.3.1

### Library (CrawlFurther.Core)
- Removed the vault challenge's strength adjustment: `ChallengeBoost`, `MonsterFactory.ChallengeStrength`,
  `TierRules.StarterChallenge`, `T2Challenge`, `T3Challenge` and `TierRules.Challenge`. A mod monster is the same
  in a challenge as in a normal game.

### Content
- `PoltergeistLimits`: the Poltergeist can't start its throw within 32 px of the hero or while the hero is in the
  shop (a postfix on `Attacks.CanAttack`), and a hex bolt that reaches the hero in either case does nothing (a
  damage hook).

### Repository
- `tools/challenge_sim.py` models the same strength in challenges as in normal games.

## 1.3.0

### Library (CrawlFurther.Core)
- `Game.ChaosMode`: the chaos game mode. `Active` is true in a game started from the main menu's Chaos entry
  (added under Play by `ChaosMenuEntry`) and for the rest of a game once it is continued. Never in the tutorial,
  vault challenges or attract mode. `Enabled` switches it off.
- `Game.ChaosSpells`: in chaos the hero holds two spells. The game's own spell slot is the first (Special); the
  second is kept with its own live instance and charge and cast with the ghost button, by exchanging the two in
  the game's slot for the cast. Buying a spell with one held fills the second slot; with two held, the game's
  prompt asks which to drop (a bot drops the cheaper). Bots swap in whichever spell is ready. `First`, `Second`
  and `Ratio` read what a player holds.
- `ChaosSpellHud`: a second special bar (blue) on the player HUD, both spell names in the hero stats panel, and
  the shop's "Replaces" line for spells rewritten for two slots.
- `Ghosts.ControlDiagrams`: the join screen's controls pictures (AtlasMenuConnect `controller_diagrams_04` to
  `_09`) repainted at run time with the ghost button, from paint steps in `art/core/ControlDiagrams.json`
  (written by `tools/sprites/control_diagrams.py`). The game's art is never copied into the mod. The redrawn
  picture plays as a clip of its own only for a player whose ghost button is the one drawn
  (`GhostControls.IsPictured`); anyone else keeps the game's picture and the text line under it.
- `Game.ContinueGame` now runs in Online Crawl games: the host's prompt is mirrored to every client and any
  player can answer it. A client never runs it.
- Self-test section 1460 checks the fields and methods chaos needs.
- Test mode: Run > Chaos in this game switches chaos on or off for the game being played. "Open everything"
  also marks every vault entry found, so all challenges can be played.

### Repository
- `tools/validate.py`: a `control-pictures` check (the paint steps parse, cover every picture the join screen
  plays, and ship in the package).

## 1.2.1

### Library (CrawlFurther.Core)
- `Game.ContinueGame`: when the hero beats the boss, the game's own prompt offers to continue (`ExtraBossAttempts`
  more tries, 2 by default) or end. Continue brings the winner back through the portal the way a failed try does.
  A continued game that runs out of tries asks again, and ending then records the last winner's win. Off in the
  tutorial, vault challenges and Online Crawl games. `Enabled` switches it off.
- `GameEvents.GameContinued(int)`: raised once a continued run is back under way, with the number of continues so
  far, for mods that change the game after a continue.
- A win counts toward `Unlocks.StatWins` once per player per game, however often the game is continued.
- Test mode: Run > Beat the boss now ends the boss fight as a win, to reach the prompt quickly.
- `TierRules.StarterDamage` and `TierRules.StarterMinHealth`: a hit multiplier and a health floor for starting
  monsters (evolve cost exactly 0, `TierRules.IsStarter`). Minions and blobs keep their base's cost and are not
  starters.
- `TierRules.StarterHealth`, `T2Health` and `T3Health`: max health multipliers by tier (`TierRules.Health`).
- `TierRules.StarterChallenge`, `T2Challenge` and `T3Challenge`: strength inside a vault challenge only, above
  or below 1. Health and hits on the hero each get the square root (`ChallengeBoost`,
  `MonsterFactory.ChallengeStrength`).
- All of these default to no change. Crawl: Further sets them so each tier matches the game's own monsters in
  normal games, and players pass its challenges about as often as the game's own (`ContentSetup`).
- `ClipBuilder.HandOff()` marks a clip that ends by handing the body to a behaviour (a charge, a carry, a dig) which
  gives control back itself. `ClipBuilder.HandsOff(clip)` tells the self-test, which no longer reports such a clip
  as never returning control.
- The self-test accepts a prefab sprite on the first frame of its sheet's own Idle when a kit swaps the body's idle
  clip for a stance (the menus keep the sheet's Idle).

### Repository
- `tools/challenge_sim.py`: a model of the vault challenge, fitted to Steam's global achievement rates, behind the
  1.2.1 monster strengths. It prints the fit and, per tier, normal-game strength against the game's own and the
  share of players passing a challenge, ours against the game's.
- `tools/sprites/bust_painter.py`: the portrait painter (cushion-lit fills, five clean tones a surface, the game's
  god-portrait look). `tools/sprites/origin_portraits.py` redraws the origin portraits with it, close up, and
  `tools/sprites/hero_bust_layers.py` paints the custom hero's portrait layers the same way for `hero_custom.py`.
- `tools/sprites/hero_gear.py` and `hero_custom.py`: the in-game headwear and face pieces are redrawn at the
  vanilla head's scale, edged in each material's own dark tone.
- `tools/sprites/zhekra_v2_t1.py` draws `ZhkRoyalGrub` (the Royal Grub's own sheet). `vhorrul_v2_t3a.py` gives the
  Fuse Scorpion four death poses.
- `tools/validate.py` (text) checks the length limit of every secret line, as the self-test does.

## 1.2.0

### Library (CrawlFurther.Core)
- The join screen's controls picture (`MenuJoinPlayer`, state `InputDiagram`) gets a line under it naming the
  player's ghost button (`GhostControls.Name`), in a copy of the god page's label text.
- A mod monster's vault page without a challenge shows `LibraryEntries.NoChallengeText` ("No challenge
  available") where the challenge lines go, in the same text.
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

### Repository
- Ghost blobs carry `BlobSpecialInput`: a player in one starts its special with the ghost button, and
  `Player.HandleAlternateInput` is skipped there, so Back only lets the player out (`PropFodder` releases on Back
  up, and the game starts a special on Back down). The gold ghost's jump-out and the mouse player's middle click
  pause give way to it in a blob with a special.
- The origin picker's blob page copied the god list after the picker had switched that list off, so its
  MenuTextMenu never ran and took no input. Every copy of the god list is now switched on when it is made. The
  blob page logs `ModBlobList: ...` when it is built and `Blob step: open / confirm / back / locked blob` as it is
  used.
- The blob choice is its own page of the origin picker, after the ghost form, instead of a row on the ghost page.
  It is a copy of the god list like the origin and form pages, one entry per blob laid over a row of starter
  boxes, with each entry's mouse hotspot set to its column. Every player's input reaches it the way it reaches
  the god list. The old row (`GhostBlobRow`) is gone.
- Text that could be cut or overlap now fits: monster tips are laid out from the drawn text (the OnGUI fallback
  stacked the title over a body taller than it allowed for), the god select's paragraphs keep to four lines
  (`PanelText`), long vault titles and the new-slot banner's lines shrink to fit, and the load banner and test panel
  wrap. `tools/validate.py` has a new `textfit` check for tips, god select texts, banner lines and pause subtitles.

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
