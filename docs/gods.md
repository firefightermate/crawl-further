# Gods

A god is a `GodDef` passed to `DeityFactory.Register` from a content pack. Both live in `CrawlFurther.Gods`.
`examples/ExampleGod/GlimmerPack.cs` registers a small one; Crawl: Further's nine gods are in
`src/CrawlFurther/Gods/<God>/<God>Pack.cs`.

## GodDef

| Field | What it does |
| --- | --- |
| `name` | Shown on the god select. Also the god's id: it must be unique |
| `text` | The perk line under the portrait |
| `flavour` | Two short lines, `\n` between them |
| `winText` | Shown when the god's player wins. Null takes the line of the god named in `copySoundsFrom` |
| `portraitArt` | Sheet of the portrait, 29 x 24: its `Portrait` animation, or `Idle` when it has none. Several frames loop |
| `copySoundsFrom` | Vanilla god whose select sound and win animation this god uses. Default `"Gholoth"` |
| `startingMonsters` | `MonsterDef` ids or vanilla prefab names. The vanilla menus show three |
| `gold` | Gold at the start of a run |
| `modifiers` | The god's own `PlayerModifier`s (a stat perk). Null for none |
| `copyModifiersFrom` | Vanilla god whose `PlayerModifier`s to use when `modifiers` is null |
| `monsters` | The god's `MonsterDef`s. `Register` builds them and links their evolutions. Leave it null if you build them yourself first |
| `perk` | Runs on every monster in `monsters` after its own `customize`: the place for a perk that lives on the monsters, such as a death spawn |
| `tips` | HUD and pause tips, keyed by prefab name (`"Mod" + MonsterDef.id`) |
| `pausePage` | The god's page in Pause > Tips, shown while a player follows the god |

## Registering

```csharp
/// <summary>The content pack: runs once the game's prefabs are loaded.</summary>
public static void Register()
{
    GlimmerFx.Build();
    DeityFactory.Register(God());
```

(from `examples/ExampleGod/GlimmerPack.cs`)

`Register` does, in order: build each `MonsterDef` in `monsters` with `perk` chained after its `customize`, link
the evolutions, add `tips` and `pausePage`, then make the `Deity` and insert it into the game's god list just
before the trial gods. Vanilla gods keep their indices, and mod gods appear after them in registration order.
Registering a name twice logs a warning and returns the first god. `DeityFactory.BuiltNames` lists the mod gods.

The god select shows the list as a grid of three rows. Columns are added as the list grows, and once the pips are
as close as they go, the grid splits into pages: up or down off a page turns it, and a mouse player can use the
wheel or the page arrows. Item indices do not change, so vanilla code (and other mods' patches on the god select)
read them as before.

## The perk

There are two kinds, and a god can have both:

- **A stat perk**: `modifiers` (or `copyModifiersFrom`), the game's own `PlayerModifier`s.
- **A perk on the monsters**: `perk` runs on every monster prefab of the god. The example gives each one a death
  spawn:

```csharp
/// <summary>Runs on every Glimmer monster after its kit: it leaves a Wisp cloud where it dies.</summary>
static void DeathWisp(GameObject go, Player p)
{
    Kit.AddDeathSpawn(p, GlimmerFx.Wisp);
    Strike.DeathAtFeet(p);
}
```

`Strike.DeathAtFeet` moves death spawns from the attack node to the feet. Call it after the kit has run, which
`perk` always is.

## Evolution trees

Each `MonsterDef` lists what it evolves into, by mod id or vanilla prefab name. Crawl: Further's Vhorrul, from
`src/CrawlFurther/Gods/Vhorrul/VhorrulPack.cs`:

```csharp
// ---- tier 1 (starters) ----
new MonsterDef { id = "Wickling", basePrefab = "EnemyGiantRat_Fireball", health = 3.5f, speedMult = 1.05f, evolveCost = 0f,
                 evolveTo = new[] { "WaxenKnight", "Chandler" }, kit = WicklingKit, customize = PyreOnDeath },
// ...
// ---- tier 2 ----
new MonsterDef { id = "WaxenKnight", basePrefab = "EnemyOrc", health = 7f, evolveCost = 2.5f,
                 evolveTo = new[] { "TallowColossus", "VhPyreWarden" }, kit = WaxenKnightKit, customize = PyreOnDeath },
// ...
// ---- tier 3 ----
new MonsterDef { id = "TallowColossus", basePrefab = "EnemyTroll", health = 12f, evolveCost = 4.5f, kit = ColossusKit, customize = PyreOnDeath },
```

- `evolveCost` is the evolution's price. The vanilla tiers cost 0, 2.5 and 4.5, and Core reads the cost as the
  tier: from 2 up, the monster's hits on the hero do 0.85x damage (0.8x from 4 up) and its special charges 1.25x
  slower. Below 0 keeps the base's cost.
- `evolveTo` replaces the base prefab's evolutions. `keepEvolutions = true` keeps the base's instead.
- `MonsterFactory.LinkEvolutions` resolves the names once the whole tree is built. `DeityFactory.Register` calls
  it for `monsters`. A missing target is logged and skipped.

Trees can be any depth and shape. Crawl: Further's own rule (3 starters, 6 tier 2, 12 tier 3, each monster with
one parent) is checked by `tools/check_trees.py` and its self-test, for its own gods only.

## Tips and the pause page

```csharp
tips = new Dictionary<string, MonsterTip>
{
    { "ModGlimmerRat", new MonsterTip("Glimmer Rat", "Lunging bite", "Dash through the hero") },
    { "ModGlimmerGrub", new MonsterTip("Glimmer Grub", "Spit a bolt", "Burst up and heal 0.5",
                                       "Heals a little with every burst") },
```

A player who takes a monster body sees its tip above their HUD panel. Write the lines for that player ("Dash
through the hero"). With its label (`Attack: `) each line stays within 60 characters. The optional passive is one
or two lines. The pause page is a `PauseTopic`; see [ui.md](ui.md#tips) for both.

## Vault pages

Every monster built through `MonsterFactory` gets a page in the vault's MONSTERS grid without any call. Give it a
line with `Vault.AddMonsterLine(id, name, line)` (one line, up to 90 characters, in the tone of the vanilla
pages). Without one it uses the tip's `vault` line (`TipRegistry.AddVaultLine`), and failing that the tip's name
and moves, with a warning in the log.

## Monster statues

Rooms between fights sometimes hold stone statues a ghost can step into. They come from the vanilla spawn group
`EnemyGroupStatue`. After the last pack, every mod final (a monster with `evolveCost` of 4 or more) joins the group
with weight `Statues.Chance` (30; vanilla entries are 20 to 100) when its carved statue exists: an animation named
`Statue_<the monster's sheet id>` on one of the sheets in `Statues.Sheets`. Add your statue sheet from your start
callback:

```csharp
Statues.Sheets.Add("ModStatues");
```

(from `src/CrawlFurther/ContentSetup.cs`). Draw the plinth's bottom row on the cell's last row, centred. A final
that `Statues.Exclude` returns true for keeps its statue art but never stands in a statue room.
