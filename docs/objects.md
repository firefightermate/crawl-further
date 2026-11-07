# Room objects

Room objects are things placed in rooms: shrines and fountains the hero uses, pads and snares that fire when
stepped on, and traps a ghost steps into and fires. Describe one with an `ObjectDef` and register it from a content
pack with `ObjectKit.Register`. Everything here is in `CrawlFurther.Objects`, and Crawl: Further's 32 objects are in
`src/CrawlFurther/Objects/ObjectPack.cs` and `ObjectPack2.cs`.

## Kinds

| `ObjKind` | Built from | Used by |
| --- | --- | --- |
| `Use` | The vanilla fountain | A player presses action next to it |
| `Touch` | The vanilla fountain | Fires when a player walks onto it |
| `Trap` | The vanilla dart turret | A ghost steps in, aims and fires it. Bots use it too, and the vanilla aim and enter arrows show |

`users` says who may use it: `ObjUser.Hero`, `Monster`, `Ghost`, or the combinations `Living` and `Anyone`.

## A usable object

```csharp
yield return new ObjectDef
{
    id = "MendSpring", name = "Mending Spring", art = "ObjMendSpring", kind = ObjKind.Use,
    vault = "A mossy basin of cold spring water",
    tip1 = "Drink: heal 3 health over 6 s",
    tip2 = "One drink, for the hero, outside a fight",
    users = ObjUser.Hero, actionText = "DRINK", uses = 1, useSound = "SoundPropActivate",
    useBox = new Vector2(30f, 22f), bodySize = new Vector2(14f, 5f),
    spawn = new ObjSpawn { weight = 9f, minFloor = 2, rooms = ObjRoom.Quiet | ObjRoom.Statue | ObjRoom.Stairs, place = ObjPlace.Open },
    onUse = u => ObjectKit.Run(HealOverTime(u.Body, SpringHeal, SpringTime)),
};
```

(from `src/CrawlFurther/Objects/ObjectPack.cs`; `HealOverTime` is a coroutine in that file)

`onUse` gets an `ObjUse`: `obj` (the `ModObject`), `player`, `pd`, `Body`, `At`, `IsHero`, `IsMonster`,
`IsGhost`, and helpers `Heal`, `Gold`, `Ecto`, `Status`, `Hurt` and `Say` (a short word over the user). Costs in
`costGold`, `costEcto` and `costHealth` are paid before `onUse` runs. `canUse` adds a condition of your own.

By default a `Use` or `Touch` object is off while the room's doors are locked (`offDuringFight`), and the hero
cannot use one in a fight (`heroInFight`), because his action button is also his attack.

## A touch object with states

```csharp
var snare = new ObjectDef
{
    id = "IronSnare", name = "Iron Snare", art = "ObjIronSnare", kind = ObjKind.Touch,
    vault = "Steel jaws hidden in the dust",
    tip1 = "Step in: 0.5 damage, held for 0.8 s",
    tip2 = "Catches heroes and monsters. Resets in 6 s",
    users = ObjUser.Living, uses = 0, rearm = 1f, touchRadius = 5f, offDuringFight = false,
    useSound = "SoundPropAction", bodySize = Vector2.zero, bounce = false,
    spawn = new ObjSpawn { weight = 8f, minFloor = 1, rooms = ObjRoom.Fight | ObjRoom.Quiet | ObjRoom.Corridor | ObjRoom.Trapped | ObjRoom.Stairs, place = ObjPlace.Anywhere, maxPerFloor = 2 },
    onUse = u =>
    {
        u.obj.Play("Snap");
        u.obj.Spent();
        u.Hurt(SnareDamage);
        u.Status(ModStatus.Root ?? FxFactory.GetStatus("StatusStuckToFloor"), "modobjsnare");
        var o = u.obj;
        o.After(SnareRearm, () => o.Rearm("Reset"));
    },
};
snare.once.Add("Snap"); snare.once.Add("Reset");
snare.then["Snap"] = "Sprung"; snare.then["Reset"] = "Idle";
```

Any animation of the sheet beyond the standard ones becomes a state that `ModObject.Play(name)` can switch to. It
loops unless listed in `once`, and `then` names the state that follows it. `ModObject` also has `Spent()`,
`Rearm(state)`, `After(seconds, action)`, `HoldOff(playerId, seconds)`, `Uses`, `IsSpent`, `Room`, a `partner` for
paired objects and a `data` dictionary for per-instance state.

## Traps

A trap lists its attacks. Each `ObjTrapAttack` plays an animation of the trap's sheet and spawns `ObjEffect`s on
given frames, offset from the trap's attack node (`node`, in pixels from the floor point):

```csharp
attacks = { Attack("Action", 2.5f, Fx(Hook, 1, 2f, Floor)) },
```

(`Attack` and `Fx` are small helpers in `ObjectPack.cs` that fill `ObjTrapAttack` and `ObjEffect`.) `aims`,
`angles`, `snap` and `startAngle` control how the ghost aims it. `difficulty` is its value in the game's trap
budget (1 is a dart turret).

## Art

One sheet per object, `"Obj" + id` unless `art` says otherwise, with the floor point at (`cellW / 2`, `cellH - 2`).

- `Use` and `Touch`: `Idle` (looping, required). Optional: `Use` (plays on use, then back to Idle), `Spent` (after
  the last use), `Off` (while a fight locks the room), `Vault` (the vault picture), and any states of your own.
- `Trap`: `Inactive`, `Activate`, `Active`, `Deactivate`, optional `Disabled`, and one animation per attack
  (default `Action`).

Components of your own go on each instance through `onSpawned`, never on the template. `customize` runs once on
the template.

## Text

`name` is the vault page title and the tip title. `vault` is one line of up to 90 characters. `tip1` and `tip2`
(up to 60 characters each) show on the HUD the first time a player meets the object in a room, and are added to
its vault page. Use plain words: no `[word]` and none of `% { | } ~`.

## Placement

After the game fills a room, each eligible room rolls once (`ObjectKit.RoomChance`, 0.38 by default) and, if it got
an object, once more for a second (`SecondChance`, 0.12). The object is picked by `ObjSpawn.weight` among those
whose rule allows the floor, the room and the environment and whose per-floor cap is not reached. Objects never go
in the start room, shops, boss rooms (including other mods' boss arenas), hero-battle rooms, the tutorial or the
attract demo.

| `ObjSpawn` | |
| --- | --- |
| `weight` | Weight among the objects a room may get. 0: never at random |
| `chance` | Its own chance per room, rolled before the shared roll, for rare finds whose odds should not depend on how many other objects are installed. Use it with `weight = 0` |
| `minFloor`, `maxFloor` | Floors it may appear on |
| `rooms`, `notRooms` | `ObjRoom` flags: `Fight`, `Quiet`, `Corridor`, `Statue`, `Trapped`, `Stairs` |
| `env` | `ObjEnv` flags: `Dungeon`, `Crypt`, `Mines`, `Caves` |
| `maxPerFloor` | Cap per floor, 0 for none |
| `place` | `ObjPlace.Open` (away from walls and doors), `Wall` or `Anywhere` |
| `pair` | Place two linked copies (`ModObject.partner`) |

`ObjectKit.SpawnIn(id, room)` and `ObjectKit.SpawnAt(id, room, pos)` place one by code. Players can switch the
random placement off or change the odds in `BepInEx/config/CrawlFurther.Objects.cfg`, whose `Force` setting
(comma-separated ids) puts the named objects in every room that can hold one, for testing.

## Vault and secrets

`Register` gives every object a page in the vault's OBJECTS grid, with the `Vault` animation (else `Idle`) as its
picture. Set `secret` to a secret's id ([ui.md](ui.md#secrets)) to have it found the first time a human player
uses, triggers or enters the object.
