# Monsters

A mod monster is a copy of a vanilla monster prefab (its body, physics, AI, sounds and hit reactions) drawn with
your sheet, with new stats and, usually, new moves. Everything here is in `CrawlFurther.Monsters`. The examples
come from `examples/ExampleGod/GlimmerPack.cs` and `GlimmerFx.cs`.

## MonsterDef

| Field | What it does |
| --- | --- |
| `id` | Unique id. The prefab is named `"Mod" + id` (`PrefabName`), which is also the key for tips, traits and statues |
| `basePrefab` | The vanilla monster to copy, for example `"EnemyGnome"`, `"EnemyOrc"`, `"EnemyMushroom"` |
| `art` | The sheet. Defaults to `id` |
| `health` | Max health. 0 or below keeps the base's |
| `speedMult` | Multiplies the base's move speed |
| `evolveCost` | The evolution cost, which Core also reads as the tier ([gods.md](gods.md#evolution-trees)). Below 0 keeps the base's |
| `specialChargeTime` | Seconds to charge the special, set after the `kit` and the tier rule. 0 or below keeps theirs |
| `attackCooldownMult` | Multiplies the cooldown of every basic attack, the `kit`'s included |
| `damageMult` | Multiplies every hit the monster lands on the hero, its behaviours' included, on top of the tier rule ([gods.md](gods.md#evolution-trees)). Statuses keep their own damage |
| `evolveTo`, `keepEvolutions` | The tree ([gods.md](gods.md#evolution-trees)) |
| `kit` | Builds the moveset: `(Player prefab, SpriteSheet sheet)` |
| `aliases` | Without a kit: maps the base's attack slots (`"Attack0"`, `"Attack1"`, `"Special"`) to animations with other names |
| `customize` | The last step, for anything else: `(GameObject prefab, Player player)` |
| `traits` | Plates, regeneration, stealth, a lifetime, behaviours of your own ([below](#traits-and-behaviours)) |

`MonsterFactory.Build(def)` makes the monster and returns its prefab's `Player`, or null with an error in the log.
`DeityFactory.Register` builds a god's `monsters` for you. Built monsters are in `MonsterFactory.Built`, by id.
`MonsterFactory.FindVanilla("EnemyOrc")` returns a vanilla monster prefab.

### What Build does

1. Clones the base prefab without running its `Awake` and parks the copy where it acts as a prefab of its own.
2. Replaces every animation (idle, run, death, knockback, portrait, statue, spawn) with one cut from your sheet.
   Each clip gets a name of its own, `Mod<sheet>_<slot>`.
3. Puts the art's feet on the transform, refits the hurtbox to 90% of the Idle frame, and frames the portrait the
   menus show.
4. Applies health, speed and cost. Unless `keepEvolutions` is set, the base's evolutions are cleared.
5. Runs `kit`, then scales its offsets by `ArtScale`, applies the tier rule and the def's own tuning
   (`damageMult`, `specialChargeTime`, `attackCooldownMult`), then runs `customize`.
6. Registers `traits` under the prefab name.

Without a kit, the base's attacks keep their own timing and events and play the animations of the same name on
your sheet: `Attack0`, `Attack1`, ..., `Special` (or the names in `aliases`). That is the quickest way to reskin a
monster, but the moves keep the base's hitboxes and effects.

## Kits

A kit replaces the moveset. The shape is always the same: take the base's first attack and special as templates
(they carry the AI and feel settings), add effect slots, build a clip per move, and swap the attacks.

```csharp
// Glimmer Grub: Spit (a bolt); Rise (bursts up, hurting what stands close, and heals itself 0.5)
static void GrubKit(Player p, SpriteSheet sh)
{
    var attacks = Kit.Attacks(p);
    var basic = attacks[0];
    var special = Kit.Special(p);
    var voice = Kit.Voice(p);
    int first = Strike.Mark(p);
    int bolt = Kit.AddEffect(p, GlimmerFx.Bolt, offsetX: 12f, offsetY: 6f);
    int burst = Kit.AddEffect(p, GlimmerFx.Burst, offsetX: 0.01f, offsetY: 4f);

    var spit = Kit.Shot(sh, "Spit", "ModGlimmerGrubSpit", 3, voice, 0f, bolt).Build();
    var rise = new ClipBuilder(sh, "Rise", "ModGlimmerGrubRise").Once()
        .Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop")
        .Ev(2, "AnimAttack", burst).EvO(2, "AnimSound", voice)
        .EvF(2, "GlimmerHeal", 0.5f)            // received by GlimmerGlow
        .Ev(-1, "AnimRun")
        .Build();

    attacks.Clear();
    attacks.Add(Kit.Attack(basic, spit, 1.6f, rangeInner: 45f, rangeOuter: 70f, retreatWhileAttacking: true));
    Kit.SetSpecial(p, Kit.Attack(special, rise, 0f, rangeInner: 0f, rangeOuter: 20f, rangeRetreat: 0f), 6f);
    Strike.Feet(p, first, 6f);
}
```

| Call | What it does |
| --- | --- |
| `Kit.Attacks(p)` | The basic attacks, a list you edit in place. The AI picks among them |
| `Kit.Special(p)` | The special attack, or null for a base without one |
| `Kit.Voice(p)` | The base's attack sound, to reuse in your clips |
| `Kit.AddEffect(p, prefab, ...)` | Adds an effect slot and returns its index for `AnimAttack(i)`. Offsets in pixels (see [placing effects](#placing-effects)). `attach`: the effect follows the monster. `destroyOnAnimEnd`: it goes when the monster's clip ends. `angle`, `angleMax` in degrees. `like`: copy another slot's settings first |
| `Kit.Melee(sheet, anim, clipName, sound, frame, slot, lunge, ...)` | A melee clip: aim freely during the wind-up, then for each (frame, slot, lunge speed) triple step forward and strike. Returns the builder |
| `Kit.Shot(sheet, anim, clipName, release, sound, stagger, slots...)` | A ranged clip: aim freely, lock on the release frame, fire every slot there (each `stagger` seconds after the last). Returns the builder |
| `Kit.Attack(template, clip, cooldown, rangeInner, rangeOuter, rangeRetreat, retreatWhileAttacking)` | A new attack from a template's settings. The AI attacks between `rangeInner` and `rangeOuter` pixels from the hero and backs off inside `rangeRetreat` |
| `Kit.SetSpecial(p, attack, charge)` | Replaces the special and its charge time (seconds) |
| `Kit.EnableSpecial(p, attack, charge)` | Gives a special to a base that had none |
| `Kit.Order(p, order, comboReset)` | How the AI picks among the basic attacks: `Attacks.eAttackOrderType.InOrder`, `Randomised` or `Combo` |
| `Kit.AddDeathSpawn(p, prefab)` | Something left behind on death |
| `Kit.Scale(p, slot, s)` | Scales the effect a slot spawns (the game ignores the slot's own scale fields) |
| `Kit.SoundGO(name)` | A vanilla sound cue by name, for `AnimSound` |

Every clip must hand control back with `AnimRun` (usually `Ev(-1, "AnimRun")`). The self-test reports a clip that
does not, and any event that nothing on the monster receives.

### Clip events the game understands

These are handled by the game's components on every monster body (`Player`, `PlayerMovement`, `Health`,
`AudioCueSource`) and used throughout Crawl: Further's kits:

| Event | Effect |
| --- | --- |
| `AnimAttack(int slot)` | Spawn effect slot `slot` |
| `AnimRun()` | The move is over: back to running |
| `AnimSound(Object cue)` | Play a sound (`EvO`) |
| `AnimInputOff()` / `AnimInputOn()` | Stop / resume reading the controls |
| `AnimInputMultiplyFreeFace(float)`, `AnimInputMultiplyStop()` | Slow movement while still turning to aim, then stop that |
| `AnimMove(float speed)`, `AnimMoveStick(float speed)`, `AnimMoveStop()` | Move forward at a speed, lunge toward the stick, stop |
| `AnimCollideOff()` / `AnimCollideOn()` | Pass through bodies, then stop passing through |
| `AnimStartInvincibility()` / `AnimStopInvincibility()` | Ignore hits for a while |
| `AnimShadowAlpha(float)` | Fade the shadow |

Core's `ModMonster`, on every mod monster, adds `ModGainPlates(int)`, `ModSprint(float seconds)`,
`ModPullHero(float strength)`, `ModStepBehindHero()` and `ModAmbush(int slot)`. Your own `MonsterBehaviour`s add
more ([below](#traits-and-behaviours)).

## Effects

An effect template is a GameObject that attacks spawn. Templates are cloned from vanilla effects, so they keep the
vanilla physics and damage setup. `FxKit` covers the common cases. Damage is in the game's
health units, knockback is a multiplier, speeds are pixels per second and times are seconds. Name templates
`Mod...`.

```csharp
/// <summary>A melee box that turns toward where the monster aims, so it can bite up and down too.</summary>
static GameObject Hitbox(string name, float damage, float knock, float life, float w, float h)
{
    var go = FxKit.BodyHit(name, damage, rate: 0.3f, knock: knock, life: life);
    AimedMelee.Rotating(go);
    Strike.HitBox(go, w, h);
    return go;
}
```

| `FxKit` | Makes |
| --- | --- |
| `Projectile(name, vanilla, art, anim, speed, life, damage, knock, status, statusChance, ...)` | A flying shot cloned from a vanilla projectile (for example `"DFX_skelMageNewProjectile"`), drawn with your animation |
| `Swipe(name, vanilla, damage, knock, ...)` | A vanilla melee swipe with new numbers |
| `BodyHit(name, damage, rate, knock, life, ...)` | An invisible hitbox that stays live for `life` seconds and hits each target every `rate` seconds. Size it with `Strike.HitBox` |
| `TimedHit(name, vanilla, art, anim, onFrame, offFrame, damage, knock, ...)` | A hitbox wearing your art that deals damage between two frames |
| `Visual(name, art, anim, loop, lifetime)` | Art only, no damage |
| `Cloud(name, art, anim, speed, damage, rate, status, statusChance, durations)` | A slow cloud that hurts every `rate` seconds while it plays |
| `MinionSpawner(name, minion, art, anim)` | Plays your art, then releases a monster |
| `Inert(name, art, anim, ...)` | Harmless, but remembers who spawned it, so what it spawns counts as theirs |
| `Emitter(name, projectile, count)` | Bursts a ring of `count` projectiles |
| `Weakened(template, name, damageMult)` | A copy with scaled damage, used for hero spells built from monster moves |
| `EchoOf(template, damageMult)` | A shadow copy that monsters with the `echo` trait repeat |

`FxFactory` is the layer underneath: `Clone(vanilla, name)`, `Reskin`, `SetEffect` (lifetime, placement, what it
spawns at the end), `SetDamage`, `SetContacts` (what happens on hit), `SetMotion`, `SetStatusZone`,
`SpawnOwned(template, pos, source)` and `Vanilla(name)` to fetch any vanilla prefab. Components of your own go on
each spawned instance through `FxFactory.OnSpawn[template]`, never on the template: Unity 5.4 cannot copy a
component from a plugin assembly when it instantiates a prefab.

### Impact puffs

Cloned effects lose the vanilla spark they showed on impact and get Core's neutral puff instead.
`ImpactFx.AddTheme(key, sheet, prefixes...)` registers a themed puff (a sheet with `Wall` and `Hit` animations,
24 x 24 cells) for effects drawn from sheets whose id, without a leading `Fx`, starts with one of the prefixes.
Call it before building the effects.

### Placing effects

`Strike` handles where effects land, and its summary in `Monsters/Strike.cs` lists three engine facts worth reading
before you write a kit. In short:

- A slot spawns at the monster's attack node plus its offset, and the node comes from the base prefab. Call
  `Strike.Mark(p)` before adding slots and `Strike.Feet(p, mark, nodeY)` after: the node moves to `nodeY` pixels
  above your art's feet and the new slots' offsets become relative to the feet. The AI aims from the node, so a
  projectile flies true when it leaves near the node's height.
- The game's pool resets a reused instance's scale to 1, so size invisible hitboxes with `Strike.HitBox` or
  `Strike.Collider`, which change the collider rather than the scale.
- Ground effects (rings, puddles) only touch the hero's feet. `Strike.Ground(go, sheet, gx, gy, w, h)` puts the
  art's pixel (gx, gy) and a w x h footprint on the spawn point. `Strike.ArtAt` sets the art's origin alone.

`AimedMelee.Rotating(template)` makes a melee box turn with the aim, so a monster can hit up and down.
`AimedMelee.Angles` adds `<anim>Up` and `<anim>Down` variants of a move.

## Traits and behaviours

`MonsterTraits` are rules for every instance of one monster. Set them with `MonsterDef.traits` (or
`MonsterTraits.Register(prefabName, traits)` before the monster first spawns):

| Field | What it does |
| --- | --- |
| `maxPlates`, `plateFx`, `plateBreakFx`, `showPlateCount` | Plates that each block one hit from the hero |
| `regenAt`, `regenPerSecond` | Regenerate while a test on the monster's position holds |
| `stealth` | Turn nearly invisible after standing still for 0.9 s |
| `hiddenAt` | Nearly invisible wherever this test holds |
| `echo`, `echoDelay`, `echoFx` | Repeat attacks that have an `EchoOf` template |
| `lifetime`, `expireFx` | Despawn after a number of seconds (summons, decoys) |
| `stealsGold` | Keep the gold-stealing hit a monster copied from a thief (the gnome) has. Off by default |
| `Add<T>()` | Add a `MonsterBehaviour` of your own to every instance |

The example's moth fades out when it keeps still, and its grub carries a behaviour:

```csharp
new MonsterDef { id = "GlimmerGrub", basePrefab = "EnemyMushroom", health = 4.5f, speedMult = 0.9f,
                 evolveCost = 0f, kit = GrubKit, traits = new MonsterTraits().Add<GlimmerGlow>() },
new MonsterDef { id = "GlimmerMoth", basePrefab = "EnemyFlyingEye_Dodge", health = 3f, speedMult = 1.1f,
                 evolveCost = 0f, kit = MothKit, traits = new MonsterTraits { stealth = true } },
```

A `MonsterBehaviour` receives clip events as methods of the same name and can run per-frame rules in `Update`.
`Monster` is the body's `ModMonster`, with `Heal`, `Face`, `FaceHero`, `HeroPos`, `AddPlate`, `OwnSource` (a damage
source for `FxFactory.SpawnOwned` and direct hits that carries the controlling player's damage modifiers, as the
game's own attacks do; `ModUtil.MonsterSource(body)` makes one for any body) and `Traits`:

```csharp
public class GlimmerGlow : MonsterBehaviour
{
    /// <summary>Clip event: heal <paramref name="amount"/> and show the heal burst.</summary>
    void GlimmerHeal(float amount)
    {
        if (Monster != null && Monster.Alive) Monster.Heal(amount);
    }
}
```

Bodies are pooled: reset anything that lasts one life in `OnEnable`. To carry settings of your own, derive from
`MonsterTraits` and read them back through `Monster.Traits`.

## Statuses and overlays

`ModStatus` replaces the vanilla crowd control, which never expired when put on a projectile:

- `ModStatus.Slow` (x0.55 speed, 1 s), `ModStatus.Root` (x0.15 speed, 0.8 s) and `ModStatus.Daze` (cannot act,
  0.6 s). A chain of them lasts at most 1.2 s, and then the target is immune to all three for 3 s.
- `FxFactory.GetStatus(name)` returns a vanilla status by name (for example `"StatusOnFire"`), and the timed
  versions in place of the vanilla slows and daze.
- `ModStatus.AllowCrowdControl(target)` lets crowd control of your own (a grab, a hold) follow the same rule.
- `ModStatus.RegisterOverlay(statusName, sheet, anim, offsetY, at)` draws a looping overlay on anyone carrying a
  status, for as long as it lasts. A sheet with `<anim>Big` uses it on large bodies.
- `ModStatus.Indicator(id, sheet, anim, offsetY, at)` makes an overlay not tied to a status. Show and hide it with
  `ModInd.Set(body, def, on, seconds)`. `ModInd` also has the shared ones: `Heal`, `Regen`, `Haste`, `Might`,
  `Plates` and `Charge`.

`FloatNumber.Show(text, tone, at)` and `FloatNumber.RollOver(body, value, max)` pop small numbers in the game's
pixel font (digits and the letters D, O, G, E).

## Ghost blobs

A ghost spawns a blob with Back. Each ghost form has its own (the Gleaner's Mote, the Binder's Gel), and a player can
pick another one on the ghost page of the origin picker, in the row under the forms. `GhostBlobs.Register` adds a blob
to that row. From `src/CrawlFurther/Ghosts/GhostPack.cs`:

```csharp
GhostBlobs.Register(new GhostBlobDef
{
    id = "King", name = "King Blob", summary = "Slams, rains globs, and costs more ectoplasm",
    prefab = pd => King.gameObject, art = "BlobKing", bodies = KingBodies,
    fits = f => f != null && f.tier != SlotTier.Normal,   // the silver and gold ghosts' own prize
});
```

- `prefab` gives the monster for a player. `art` names the sheet whose Portrait frame is drawn as a dark outline
  while the blob is locked.
- `unlock` is a challenge id (see [ui.md](ui.md#challenges)). The blob stays locked until it is done; null means
  always open.
- `fits` says which forms may pick it; null means every form.
- `bodies` is what one costs in bodies of ectoplasm. The game charges one; the rest is charged the same way, and Back
  does nothing (the stored bodies blink) while the ghost has fewer.

The row lists the form's own blob first, then every blob that fits the form, open or locked, leaving out the one that
is the form's own anyway. Picks are kept per player in `GhostBlobs.Chosen`. `GhostBlobs.ChoiceOf(player)` gives the
pick in effect (null for the form's own: a pick that does not fit the form, or is locked, counts as no pick) and
`GhostBlobs.PrefabOf(player, own)` what Back spawns. Bots always spawn their form's own. A mod that owns the forms sets
`GhostBlobs.OwnOf`, so the row can show each form's own blob.
