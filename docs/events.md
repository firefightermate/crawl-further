# Events

Core patches the game at the moments most mods care about and raises C# events there, so a mod can react without a
Harmony patch of its own. Each handler runs on its own: one that throws is logged with its name and stops neither
the other handlers nor the game. Subscribe from your start callback, never from `Awake` (these classes name game
types).

## GameEvents (namespace `CrawlFurther`)

| Event | When |
| --- | --- |
| `GameReady` | Once, after every content pack has registered and before the self-test runs |
| `RunStart` | A new run starts (`SystemGame.OnStartGame`), before its first floor |
| `FloorStart` | A floor starts, once its players are set up (`SystemPlayers.OnLevelStart`) |
| `RoomChanged(Room)` | The hero walked or teleported into a room, the floor's first room included |
| `MonsterSpawned(Player)` | A monster has been set up in the level (`SystemLevel.OnMonsterSpawned`) |
| `HeroDamaged(DamageInfo)` | A hit landed on the hero. Blocked or cancelled hits are not reported. `m_amount` is the damage dealt |

The example counts how often its monsters hit the hero in a run (`examples/ExampleGod/GlimmerEvents.cs`):

```csharp
public static void Subscribe(ManualLogSource log)
{
    GameEvents.RunStart += () => s_hits = 0;
    GameEvents.HeroDamaged += hit =>
    {
        var attacker = hit.m_source != null ? hit.m_source.m_sourceOwner : null;
        if (GlimmerPack.IsGlimmer(attacker)) s_hits++;
    };
    GameEvents.FloorStart += () => log.LogInfo("Glimmer monsters have hit the hero " + s_hits + " times this run");
}
```

`Further.IsReady` is true once every pack has registered.

## MonsterEvents (namespace `CrawlFurther.Monsters`)

| Event | When |
| --- | --- |
| `PlayerAwake(Player)` | A body woke (`Player.Awake`): once per instance, pooled ones included. Mod monsters already have their `ModMonster` |
| `AttackSpawned(Player attacker, GameObject instance, GameObject template)` | An attack of the hero or a monster spawned an effect |

`AttackSpawned` is how Crawl: Further's gods react to their own moves. Vhorrul, from
`src/CrawlFurther/Gods/Vhorrul/VhorrulPack.cs`:

```csharp
static void OnAttackSpawned(Player owner, GameObject fx, GameObject template)
{
    if (owner == null || fx == null) return;
    if (owner.gameObject == ModUtil.Hero()) { VhPoppetFx.HeroStruck(fx.transform.position); return; }
    var q = owner.GetComponent<VhorrulBehaviour>();
    if (q != null) q.OnAttackSpawned(fx, template);
}
```

## Hooks

- `ItemRegistry.AddDamageHook((health, hit, attacker) => ...)` runs inside `Health.Damage` for every hit, before
  it lands. It can change the damage or cancel the hit ([items.md](items.md#item-effects-on-hits)).
- `FxFactory.OnSpawn[template]` runs on every spawned instance of an effect template.
- `ObjectDef.onSpawned` runs on every spawned room object.
- `TestMode.SwitchedOff` runs when an online match turns test mode off ([testing.md](testing.md)).

## When you still need Harmony

For anything else, write `[HarmonyPatch]` classes and apply them with `FurtherMod.PatchAll()` from your start
callback. It patches one class at a time, so one bad patch is logged and does not stop the others. Class order is
by full name, which does not depend on file layout.

At equal priority Harmony runs patches on the same method in the order they were applied. When two of your classes
patch one method and the order matters, pass their class names to `PatchAll` and they are applied first, in that
order. Crawl: Further does this in `src/CrawlFurther/Plugin.cs` (`s_mod.PatchAll(PatchOrder)`).

Core applies its own patches after every mod's start callback, so patches applied there run before Core's on a
method both patch. The self-test's "harmony patch classes" section runs every patch class's static setup once, so a
reflection lookup that would throw inside the game shows up in the report instead.
