# Menus, tips and the rest of the UI

Everything here is in `CrawlFurther.UI`. Text that a player reads is plain words: the game's text drops any
`[word]`. Secrets, challenges and room objects also must not use `% { | } ~`.

## The violet gem

Anything drawn from a sheet loaded through Core counts as mod content and gets one small violet gem in the menus
(portraits, shop pictures, vault cells, the evolve screen), with no call from your mod. `ModGem.Exclude(sheetId)`
leaves a sheet unmarked; `ModMark.MarkArt(atlas)` counts art you compose at run time as mod art.

Every gem is placed through `ModMark`, and each entry has one owner of its mark: a vault entry's cell (not the big
picture below it), a shop item's pedestal (not the popup), the violet pip of a god or origin in its list (not the
portrait; an entry whose pip is another colour is marked on its portrait). Never paint the gem into your art:
`tools/validate.py` fails on it. Players can turn the gems off with `ModGem` in `CrawlFurther.UI.cfg`.

## Vault pages

The vault is the main menu's library. Some pages come without any call:

- every monster built by `MonsterFactory` (MONSTERS grid; text from `Vault.AddMonsterLine` or the tips, see
  [gods.md](gods.md#vault-pages)),
- every item and weapon registered with `ItemRegistry` (ITEMS and WEAPONS),
- every room object registered with `ObjectKit` (OBJECTS).

For a `Powerup` or room prop built some other way, call `Vault.AddItem(powerup)` or
`Vault.AddObject(prefab, name, description, portrait)`.

### A category of your own

`Vault.AddCategory` adds a category before BACK, shown as a picture grid. Crawl: Further's FURTHER and SECRETS
categories, from `src/CrawlFurther/Library/FurtherVault.cs`:

```csharp
static readonly VaultCategory s_further = new VaultCategory
{
    label = "FURTHER",
    stamp = "VaultStampFurther",
    summary = (found, total) => found + " / " + total + " entries found\n\nThe gods, hero origins, ghost forms and blobs of " + Name + ", each with its own page",
    pages = Pages,
    selfCheck = SelfCheck,
};

static readonly VaultCategory s_secrets = new VaultCategory
{
    label = "SECRETS",
    stamp = "VaultStampSecrets",
    summary = (found, total) => found + " / " + total + " secrets found\n\nRiddles that point to the rarest finds in " + Name,
    secrets = true,
};
```

- `label` is the menu text, in capitals. `stamp` is a sheet whose frame 0 (59 x 48) shows while the category is
  highlighted. `summary` turns (found, total) into the text under the list.
- `pages` returns `VaultPage`s and is called once, after every content pack. A page has `kind` and `id` (together
  they make its save key, so keep them stable once released), `name`, `text` (one or two lines), `art` (a sheet:
  its `Portrait`, else `Vault`, else `Idle`), and optionally `unlock` (a challenge id) or `locked` (a test) to show
  a padlock until it opens.
- A category with no pages is not listed. Register categories from your start callback.

## Secrets

A secret is something rare a player can find. Its vault page shows a riddle and how rare it is until it is found,
then its name, picture and text. A new find is announced with a banner on the next menu.

- `Secrets.Add(new SecretDef { id, name, riddle, rarity, text, iconSheet, group })`. Limits: riddle 75 characters,
  rarity 30, text 120.
- `Secrets.AddMonster(prefabId, group, riddle, rarity)` makes a secret of a built mod monster. It is found when a
  human player becomes that monster.
- `Secrets.Found(id)` marks a secret found from your own game code. An `ObjectDef.secret` does it for room objects.
- `Secrets.AddGroup(name, hiddenTitle, banner)` sets the order the vault lists groups in and the title of a page
  that is still hidden.

Found secrets are saved in `BepInEx/config/CrawlFurther.Secrets.cfg`. The pages appear in a category registered
with `secrets = true`. Crawl: Further registers one (SECRETS); a mod that runs without Crawl: Further must register
its own.

## Challenges

A challenge is done when a counter reaches a target. Counters persist across games in
`BepInEx/config/CrawlFurther.Unlocks.cfg`. From `src/CrawlFurther/Gods/SlotChallenges.cs`:

```csharp
Unlocks.Add(new UnlockDef { id = Unlocks.IdFor(list, tier), title = title, text = text, stat = stat, target = target, slot = slot, tier = tier });
```

`title` is short and in capitals, `text` one line of up to 40 characters ("Evolve your monsters 60 times"), and
`slot` names what it opens on the banner (`"SILVER IDOL"` shows as `SILVER IDOL UNLOCKED`). Core counts these for human
players: `Unlocks.StatHeroKills`, `StatWins`, `StatEvolutions`, `StatFinals`, `StatEcto` and `StatHeroSlain`.
Count your own with `Unlocks.Count(stat, n)`, `CountFraction` or `CountDistinct(stat, key)`. Check one with
`Unlocks.IsUnlocked(id)` and show progress with `ProgressText(id)`.

## Tips

### HUD monster tips

A player who takes a monster body sees its tip above their HUD panel, and the first Pause > Tips page repeats it.
Tips are keyed by prefab name. `TipRegistry.Add(key, tip, group)` adds one, and `GodDef.tips` does it for a god's
monsters, with the god's pause page id as the group ([gods.md](gods.md#tips-and-the-pause-page) has the example's). A `MonsterTip` is a name,
one line for the basic attack, one for the special, and an optional passive of one or two lines (`\n` between
them). Write them for the player who is the monster, within 60 characters each including the label. Players choose
who sees tips (Tips: ALL, P1 ONLY or OFF) and when (Tooltips: ALWAYS, FIRST TIME or OFF) in the options menu. FIRST
TIME shows a monster's tip only the first time that player's save takes it (`BepInEx/config/CrawlMod.TipsSeen.txt`).

`TipRegistry.AddAlias(key, sameAs)` shares a tip, and `TipRegistry.AddVaultLine(key, name, line)` gives a monster a
vault line from the tip data. Crawl: Further keeps its tips in `data/tips/tips_<group>.json`, which
`tools/merge_tips.py` checks and turns into C# tables.

### Pause pages

A `PauseTopic` is one tab of Pause > Tips: an id, the god's name for a god's page (empty otherwise), a header of up
to 8 capitals, a short subtitle and paragraphs.

```csharp
pausePage = new PauseTopic("glimmer", "Glimmer", "GLIMMER", "lamps and moths", new[]
{
    "When a " + PauseTips.Hi("Glimmer") + " monster dies it leaves a wisp that stings the hero for a second.",
    "- The Grub heals 0.5 each time it bursts up.",
    "- The Moth fades from sight while it keeps still.",
}),
```

(from `examples/ExampleGod/GlimmerPack.cs`)

Paragraphs are wrapped at run time into pages of 7 lines. `PauseTips.Hi(word)` colours a word, and a paragraph
starting with `- ` is a bullet. The topics of the gods in the current game come first, then the game's own pages,
then the ids in `TipRegistry.TopicOrder`, then the rest. Add a topic that is not a god's with
`TipRegistry.AddTopic`.

## Branding

`Branding.Set(BrandingDef)` puts a mod's name and version on the title screen and can add a wordmark next to every
CRAWL logo, flame pips beside the selected main menu item and drifting embers. Every sheet is optional, and the
last call wins, so this is for a mod that wants to be the face of the game. Crawl: Further's call, from
`src/CrawlFurther/ContentSetup.cs`:

```csharp
Branding.Set(new BrandingDef
{
    name = Plugin.NAME, version = Plugin.VERSION,
    wordmark = "BrandFurther", spark = "BrandSpark", menuPip = "BrandPip", menuMote = "BrandMote",
});
```

The animations each sheet needs are listed on `BrandingDef`. Players can switch the wordmark and the menu dressing
off in `BepInEx/config/CrawlFurther.UI.cfg`.

## Music

`ModMusic.AddFolder(folder)` adds every `.ogg` and `.wav` in a folder to a pool of tracks. When the game starts a
piece of gameplay music, a roll (`CustomMusicChance` in `CrawlFurther.UI.cfg`, about 1 in 3 by default) may play one
of them instead, never the same one twice in a row. Boss, level 10, win and lose music are never replaced. Call it
from your start callback. `tools/music_convert.sh` converts and normalises tracks.

## HUD timers

`HudTimers.Set(playerId, key, secondsLeft, icon, paused)` shows a small countdown beside a player's HUD panel:
the icon (frame 0 of a sheet's `Idle`) and the whole seconds left. Your code owns the clock: call `Set` whenever the
time changes and `HudTimers.Clear(playerId, key)` when the effect ends. `paused` dims a timer that is waiting, for
example one that only runs during fights.
