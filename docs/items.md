# Items and weapons

Shop items (spells, artifacts, potions) and hero weapons are copies of vanilla prefabs with new names, prices,
pictures and effects. Register them from a content pack with `ItemRegistry.Register`. Everything here is in
`CrawlFurther.Items`.

## Shop items

```csharp
public static readonly ItemDef Volley = new ItemDef
{
    id = VolleyId,
    cloneFrom = "SpellFetidDischarge",
    group = "GroupSpellsPurchasable",
    name = "Glimmer Volley",
    description = "Fire a fan of 3 glimmer bolts, 0.45 damage each",
    cost = 40,
    bubbleArt = "IconGlimmerVolleyBubble",
    customize = (go, item) =>
    {
        // the hero's copy hits monsters; 0.6 x 0.75 = 0.45 damage
        var bolt = FxKit.Weakened(GlimmerFx.Bolt, "ModHeroGlimmerBolt", 0.75f);
        foreach (var slot in R.Get<List<DamageEffectData>>(item, "m_specialAttackDamageEffects")) slot.m_object = bolt;
    },
};
```

(from `examples/ExampleGod/GlimmerItems.cs`)

| Field | What it does |
| --- | --- |
| `id` | Unique id. The prefab is `"Mod" + id`, and the shop pedestal picture is the animation named `id` |
| `cloneFrom` | The vanilla `Powerup` to copy: its behaviour, effects and sounds |
| `name`, `description` | Shop text. The game's text drops any `[word]`, so keep to plain words. Give real numbers |
| `cost` | Price in gold |
| `bubbleArt` | Sheet of the shop pop-up picture (animation `Bubble`). Null keeps the vanilla one |
| `hudArt` | Sheet of the HUD icon (animation `Hud`). Null keeps the vanilla one |
| `group` | The vanilla shop group that sells it: `GroupSpellsPurchasable`, `GroupArtifactsPurchasable` or `GroupPotionsPurchasable` |
| `customize` | Runs on the new prefab before it is registered: rewire effects and modifiers here |

`ItemRegistry.Register(def)` returns the new `Powerup`, or null when `cloneFrom` is not found. Items are in
`ItemRegistry.Items` by id, and each gets a page in the vault's ITEMS grid.

Most new items come from one of a few vanilla bases whose behaviour fits, with the effect slots swapped. The private
fields (`m_specialAttackDamageEffects`, `m_effects`, `m_modifiers`) are reached with `R.Get` and `R.Set` from
`CrawlFurther.Util`; `R.Get` throws `MissingFieldException` for a name that does not exist. A monster effect
reused for the hero should go through `FxKit.Weakened`, which makes a separate template with scaled damage.
Crawl: Further's items are in `src/CrawlFurther/Items/ItemPack*.cs`.

### The shop pedestal

The shop shows each purchasable standing on a pedestal. Vanilla looks the picture up in its own atlas, where a mod
item is missing, so mods draw pedestal pictures on 35 x 33 cells (the item at the bottom centre), one animation per
purchasable named after it, and register the sheet once from the start callback:

```csharp
/// <summary>Things to set up before any content pack runs. Called from the plugin's start callback.</summary>
public static void Setup()
{
    ShopPedestal.AddSheet(PedestalSheet);
}
```

An item uses the animation `<id>` and a weapon `Wpn<id>`. An item without a picture shows a vanilla stand-in and
logs a warning.

### Item effects on hits

`ItemRegistry.AddDamageHook((health, hit, attacker) => ...)` runs inside `Health.Damage` for every hit the game
would land, after Core's tier scaling and before a monster's plates. It may change `hit.m_amount`, and returning
true cancels the hit. Hooks run in the order they were added.

## Weapons

A `WeaponDef` copies a vanilla `Weapon` prefab. The hero keeps the base weapon's frames and sounds, and the
attacks are retimed and fire your effects. From `src/CrawlFurther/Weapons/WeaponPack.cs`:

```csharp
new WeaponDef { id = "Gravehook", name = "Gravehook", family = "Tether", baseWeapon = "WeaponSpear", baseCombo = 1,
    cost = 85, damageMult = 0.95f, comboCooldown = 0.4f,
    description = "Two jabs (1.0 dmg), then a thrown hook (0.95) that drags the monster it catches back to your feet",
    effects = () => L(Melee(WeaponFx.HookJab, 14f, 2f, 3f, 3f), Fire(WeaponFx.Hook, 0f, -2f)),
    attacks = { new WeaponAttack(0, 0.33f, 1.0f, "a1", 0), new WeaponAttack(1, 0.40f, 0.95f, "a1", 0), new WeaponAttack(5, 0.55f, 1.1f, "a0", 1) } },
```

(`L`, `Melee` and `Fire` are that file's helpers that build the effect list.)

| Field | What it does |
| --- | --- |
| `id` | Unique id. The prefab is `"ModWeapon" + id`, the pedestal animation `Wpn<id>`, the shop bubble the sheet `IconWpn<id>Bubble` (animation `Bubble`) |
| `name`, `description`, `cost` | Shop text and price |
| `baseWeapon` | The vanilla weapon: hero frames, sounds, bot behaviour and aiming, for example `"WeaponSpear"` |
| `baseCombo` | The base combo whose idle pose and colours to keep, or -1 |
| `damageMult`, `comboCooldown` | The combo's damage multiplier and the pause after it |
| `effects` | Builds the effect list once. `AnimAttack` indices in `attacks` point into it |
| `attacks` | One `WeaponAttack(src, cooldown, scale, pairs...)` per swing: the base attack to copy, the pause after it, a frame-time multiplier, and pairs that re-point the base clip's events. `"a1", 0` sends the base's `AnimAttack(1)` to effect 0, `"m<tag>"` does the same for an `AnimMagic(tag)`. Events not listed are dropped |
| `shopChance` | Weight in the weapon shop group. Default 25 |
| `heroFrames` | Optional: points the base weapon's hero frames at redrawn ones with your weapon in hand |
| `family` | A label for logs |

Mod weapons have no random enchantments and no status rolls. `ItemRegistry.Register(weaponDef)` returns the
`Weapon` and records it in `ItemRegistry.Weapons`. Weapons get vault pages too.
