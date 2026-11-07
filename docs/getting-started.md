# Getting started

This page walks through `examples/ExampleGod`, a complete mod built only on Crawl Further Core. It adds a god
called Glimmer with three starting monsters and a shop spell. Read it next to the source. Every snippet below is
copied from it, and `./build.sh` compiles it with the rest of the repo, so the code here builds against the
current API.

What you need first: Crawl with BepInEx 5 and Crawl: Further installed (Core ships inside it, see the
[README](../README.md)), and a way to compile C# 7.3 for .NET 3.5 ([building.md](building.md)).

## How a mod starts

Crawl runs on Unity 5.4. If a plugin's `Awake` loads the game's assembly (`Assembly-CSharp`) before the engine has
registered its scripts, every script in the game breaks ("referenced script is missing"). So a mod built on Core
does nothing in `Awake` except register itself:

```csharp
[BepInPlugin(GUID, NAME, VERSION)]
[BepInDependency(FurtherCore.GUID)]
public class ExampleGodPlugin : BaseUnityPlugin
{
    public const string GUID = "com.example.crawl.examplegod";
    public const string NAME = "Example God";
    public const string VERSION = "1.0.0";

    static FurtherMod s_mod;

    void Awake()
    {
        s_mod = Further.AddMod(this, OnBooted);
    }

    /// <summary>Runs once the game has booted, before any content pack.</summary>
    static void OnBooted()
    {
        s_mod.PatchAll();
        GlimmerPack.Setup();
        Further.AddPack("Glimmer", GlimmerPack.Register);
        GlimmerEvents.Subscribe(s_mod.Log);
        GlimmerTests.Register();
    }
}
```

Keep the plugin class free of game types, fields included. Loading the class would load the game's assembly with it.

There are three stages:

1. **`Awake`**: `Further.AddMod(this, start)` records the mod. `[BepInDependency(FurtherCore.GUID)]` makes BepInEx
   load Core first.
2. **The start callback** (`OnBooted` here) runs once the game has drawn its first frames, in the order mods
   called `AddMod`. Core adds `<your plugin folder>/art` to the folders it searches for sprite sheets. Apply your
   Harmony patches here (`FurtherMod.PatchAll` applies every `[HarmonyPatch]` class in your assembly, one class at a
   time) and queue your content packs.
3. **Content packs** (`Further.AddPack(name, register)`) run once the game's gods and monster prefabs are loaded,
   in the order they were added, each exactly once. Build your content here. A pack that
   throws is logged and skipped, and the others still run. After the last pack, Core raises
   `GameEvents.GameReady` and runs the self-test.

`FurtherMod` also gives you `Log` (your BepInEx log), `Config` (`BepInEx/config/<GUID>.cfg`), `Harmony` and
`Dir` (your plugin folder). `Further.Config("Name.cfg")` returns a shared config file of any other name.

## The art

Each sheet is a PNG and a JSON file of the same name in the mod's `art/` folder:

```
examples/ExampleGod/art/
  GlimmerRat.png      GlimmerRat.json       a monster: Idle, Run, Bite, Dash, Death, Dead, Statue, Knockback, Portrait
  GlimmerGrub.png     GlimmerGrub.json
  GlimmerMoth.png     GlimmerMoth.json
  DeityGlimmer.png    DeityGlimmer.json     the god's portrait (29 x 24)
  FxGlimmerBolt.png   FxGlimmerBolt.json    a projectile
  FxGlimmerWisp.png   FxGlimmerWisp.json    the god's perk
  IconGlimmerVolleyBubble.png/.json        the spell's shop picture
  GlimmerPedestals.png/.json               the spell standing on its shop pedestal
```

The example's sheets are recoloured copies of Crawl: Further sheets, made by `tools/make_art.py`. The format,
and how to draw your own, is in [art.md](art.md). Sheet ids are global: every mod's art folder is searched, so
give your sheets a prefix of your own.

## Effects

Attacks spawn effect templates: hitboxes, projectiles, clouds. Build them before the monsters that use them.
`GlimmerFx.cs` makes all of the example's effects with the ready-made helpers in `FxKit`:

```csharp
Bolt = FxKit.Projectile("ModGlimmerBolt", "DFX_skelMageNewProjectile", "FxGlimmerBolt", "Fly",
                        speed: 150f, life: 1.5f, damage: 0.6f, knock: 0.4f);
```

This clones the vanilla skeleton mage's bolt (its collider, physics layer and damage wiring), draws it with the
`Fly` animation of `FxGlimmerBolt`, and sets new numbers. Template names start with `Mod`: Core and Online Crawl
use the prefix to tell mod objects apart. More in [monsters.md](monsters.md#effects).

## Monsters

A monster is a vanilla monster's body (physics, AI, sounds) wearing your sheet. `MonsterDef` names the body and
the new stats, and `kit` builds the moveset:

```csharp
new MonsterDef { id = "GlimmerRat", basePrefab = "EnemyGiantRat_Fireball", health = 3.5f, speedMult = 1.05f,
                 evolveCost = 0f, kit = RatKit },
```

The prefab is named `"Mod" + id` (`ModGlimmerRat`), and the sheet defaults to the id. The kit replaces the base's
attacks with clips cut from the sheet:

```csharp
// Glimmer Rat: Bite (lunges in); Dash (a 60 px charge that hits everything on the way)
static void RatKit(Player p, SpriteSheet sh)
{
    var attacks = Kit.Attacks(p);
    var basic = attacks[0];
    var special = Kit.Special(p);
    var voice = Kit.Voice(p);
    int first = Strike.Mark(p);
    int bite = Kit.AddEffect(p, GlimmerFx.Bite, attach: true, destroyOnAnimEnd: true, offsetX: 10f, offsetY: 6f);
    int dash = Kit.AddEffect(p, GlimmerFx.DashHit, attach: true, destroyOnAnimEnd: true, offsetX: 4f, offsetY: 6f);

    var biteClip = Kit.Melee(sh, "Bite", "ModGlimmerRatBite", voice, 3, bite, 85f).Build();
    // 330 px/s over the four 0.045 s sprint frames: about 60 px
    var dashClip = new ClipBuilder(sh, "Dash", "ModGlimmerRatDash").Once()
        .EvF(0, "AnimInputMultiplyFreeFace", 0f)
        .Ev(2, "AnimInputMultiplyStop").Ev(2, "AnimInputOff").EvF(2, "AnimMove", 330f).Ev(2, "AnimCollideOff")
        .Ev(2, "AnimAttack", dash).EvO(2, "AnimSound", voice)
        .Ev(6, "AnimMoveStop").Ev(6, "AnimCollideOn")
        .Ev(-1, "AnimRun")
        .Build();

    attacks.Clear();
    attacks.Add(Kit.Attack(basic, biteClip, cooldown: 1.2f, rangeInner: 14f, rangeOuter: 30f));
    Kit.SetSpecial(p, Kit.Attack(special, dashClip, 0f, rangeInner: 25f, rangeOuter: 66f, rangeRetreat: 0f), charge: 5.5f);
    Strike.Feet(p, first, 6f);
}
```

In order: take the base's first attack and its special as templates (they carry the AI settings), add effect
slots, build one clip per move (each clip event fires on a frame of the animation), swap the attacks, and move
the attack node to 6 px above the art's feet. [monsters.md](monsters.md) explains each call.

## The god

A `GodDef` describes everything the god select shows and owns the monsters:

```csharp
return new GodDef
{
    name = "Glimmer",
    text = "Dead monsters leave a stinging wisp",
    flavour = "A lamp that never goes out,\nand the things that gather to it.",
    portraitArt = "DeityGlimmer",
    startingMonsters = new[] { "GlimmerRat", "GlimmerGrub", "GlimmerMoth" },
    monsters = Monsters.ToArray(),
    perk = DeathWisp,
```

`DeityFactory.Register` builds every monster in `monsters`, runs `perk` on each one, links their evolutions, adds
the tips and pause page, and puts the god in the god list. The pack's register method ties it together:

```csharp
/// <summary>The content pack: runs once the game's prefabs are loaded.</summary>
public static void Register()
{
    GlimmerFx.Build();
    DeityFactory.Register(God());
    Vault.AddMonsterLine("GlimmerRat", "Glimmer Rat", "A rat with a lamp for a tail. It bites, then charges.");
    Vault.AddMonsterLine("GlimmerGrub", "Glimmer Grub", "Spits bolts of cold light and heals as it bursts up.");
    Vault.AddMonsterLine("GlimmerMoth", "Glimmer Moth", "Puffs sparks that daze and fades from sight when still.");
    GlimmerItems.Register();
}
```

The example's monsters do not evolve, which keeps it short. A full god has 3 starters, each evolving into two
tier-2 monsters and each of those into two tier-3 finals. [gods.md](gods.md) shows how.

## The spell

`GlimmerItems.cs` copies the vanilla Fetid Discharge, which fires three shots in a fan, and swaps its shots for a
hero-side copy of the grub's bolt. See [items.md](items.md).

## Build and install

`./build.sh` writes `build/ExampleGod.dll` next to Core and the content mod. To try it, make this folder:

```
BepInEx/plugins/ExampleGod/
  ExampleGod.dll
  art/            (the contents of examples/ExampleGod/art)
```

Start the game. Glimmer is on the god select after the vanilla gods, its monsters
have pages in the vault, and Glimmer Volley can turn up in the spell shop. If something failed,
`BepInEx/plugins/CrawlFurther/CrawlMod_selftest.txt` lists it. The self-test checks every monster built through
Core, whatever mod it came from.

With test mode on ([testing.md](testing.md)), the F2 panel has a Glimmer page: become any of the three monsters,
spawn one to fight, or give the hero the spell.

## Where next

- [art.md](art.md): the sheet format, clips, loading and exporting the game's own art
- [gods.md](gods.md): gods, trees, portraits, tips, statues
- [monsters.md](monsters.md): `MonsterDef`, kits, effects, traits, behaviours, statuses
- [items.md](items.md): shop items and weapons
- [objects.md](objects.md): room objects and traps
- [ui.md](ui.md): vault pages, secrets, challenges, branding, tips, music, HUD timers
- [events.md](events.md): game events instead of Harmony patches
- [compat.md](compat.md): working alongside Online Crawl, CrawlAPI or other boss mods
- [testing.md](testing.md): the test panel
- [building.md](building.md): compiling, the tools, packaging
