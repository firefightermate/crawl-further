using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Items
{
    using CrawlFurther.Art;
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Shop items and weapons added by mods. <see cref="Register(ItemDef)"/> and <see cref="Register(WeaponDef)"/> build
    /// the prefab from a vanilla one, put it in a shop group and record it here; the vault, the shop pedestals, the
    /// custom hero picker and the self-test read these tables. Call them from a content pack (see
    /// <see cref="ContentManager.AddPack"/>), when the vanilla prefabs are loaded.
    /// </summary>
    public static class ItemRegistry
    {
        /// <summary>Every mod shop item by id (prefab "Mod" + id), in the order registered.</summary>
        public static readonly Dictionary<string, Powerup> Items = new Dictionary<string, Powerup>();
        /// <summary>Every mod weapon by id (prefab "ModWeapon" + id), in the order registered.</summary>
        public static readonly Dictionary<string, Weapon> Weapons = new Dictionary<string, Weapon>();

        public const string WeaponShopGroup = "GroupWeaponsPurchasable";

        static readonly List<Func<Health, DamageInfo, GameObject, bool>> s_damageHooks = new List<Func<Health, DamageInfo, GameObject, bool>>();

        /// <summary>
        /// Add a hook for item effects on hits: it runs inside Health.Damage, after Core's tier damage scaling and before
        /// a monster's plates, for every hit the game would land. It may change damage.m_amount; returning true cancels the
        /// hit. Arguments: the health being hit, the hit, the attacker (may be null). Hooks run in the order added.
        /// </summary>
        public static void AddDamageHook(Func<Health, DamageInfo, GameObject, bool> hook)
        {
            if (hook != null) s_damageHooks.Add(hook);
        }

        /// <summary>Run the damage hooks; true once one cancels the hit.</summary>
        internal static bool RunDamageHooks(Health health, DamageInfo damage, GameObject attacker)
        {
            foreach (var h in s_damageHooks) if (h(health, damage, attacker)) return true;
            return false;
        }

        /// <summary>Build a shop item from <paramref name="def"/> and sell it from its shop group. Null if the vanilla
        /// prefab to copy is missing.</summary>
        public static Powerup Register(ItemDef def)
        {
            var src = FxFactory.Vanilla(def.cloneFrom);
            if (src == null) return null;
            var go = MonsterFactory.ClonePrefab(src, "Mod" + def.id);
            var pu = go.GetComponent<Powerup>();
            pu.m_displayName = def.name;
            pu.m_description = def.description;
            pu.m_cost = def.cost;
            var bubble = Icon(def.bubbleArt, "Bubble");
            if (bubble != null) R.Set(pu, "m_animPurchasableBubble", bubble);
            var hud = Icon(def.hudArt, "Hud");
            if (hud != null) R.Set(pu, "m_guiIcon", hud);
            if (def.customize != null) def.customize(go, pu);
            Items[def.id] = pu;
            if (!SellFrom(def.group, go, 100f)) FurtherCore.Log.LogWarning("Shop group not found: " + def.group);
            FurtherCore.Log.LogInfo("Item built: " + def.name + " (" + def.cloneFrom + ")");
            return pu;
        }

        /// <summary>Build a weapon from <paramref name="def"/> and sell it from <see cref="WeaponShopGroup"/>. Null if the
        /// base weapon is missing.</summary>
        public static Weapon Register(WeaponDef def)
        {
            var baseGo = FxFactory.Vanilla(def.baseWeapon);
            var baseW = baseGo != null ? baseGo.GetComponent<Weapon>() : null;
            if (baseW == null) { FurtherCore.Log.LogError("Weapon base missing: " + def.baseWeapon); return null; }
            var go = MonsterFactory.ClonePrefab(baseGo, "ModWeapon" + def.id);
            var w = go.GetComponent<Weapon>();

            w.m_weaponName = def.name;
            w.m_weaponDescription = def.description;
            w.m_cost = Mathf.RoundToInt(def.cost);
            w.m_shouldBotPurchase = true;
            var bubbleSheet = SpriteSheets.Get("IconWpn" + def.id + "Bubble");
            if (bubbleSheet != null) w.m_animationPurchasableBubble = new ClipBuilder(bubbleSheet, "Bubble", "ModWpn" + def.id + "Bubble").Loop().Build();

            // one combo: this weapon's own attack list, multiplier and cooldown (the shop shows the combo's name)
            Combo combo = def.baseCombo >= 0 && def.baseCombo < baseW.m_combos.Count ? R.Clone(baseW.m_combos[def.baseCombo]) : new Combo();
            combo.m_name = def.name;
            combo.m_description = def.description;
            combo.m_costMultiplier = 1f;
            combo.m_comboCooldown = def.comboCooldown;
            combo.m_damageMult = def.damageMult;
            combo.m_speedMult = 1f;
            combo.m_attacks = (1 << def.attacks.Count) - 1;
            combo.m_relativeDamage = baseW.m_relativeDamage;
            combo.m_relativeSpeed = baseW.m_relativeSpeed;
            combo.m_relativeRange = baseW.m_relativeRange;
            combo.m_powerup = null;
            combo.m_playerColorSwap = new ColorSwap[0];
            w.m_combos = new List<Combo> { combo };

            // the hero holding this weapon: idle and run copies of the clips the game picks for an unenchanted weapon
            // (the combo's own pose if it has one, else the weapon's)
            var noEvents = new Dictionary<string, int>();
            var idle = HeroClip(combo.m_animationIdle ?? baseW.m_animationIdle, "ModW_" + def.id + "_idle", 1f, noEvents, def.heroFrames);
            var run = HeroClip(combo.m_animationRun ?? baseW.m_animationRun, "ModW_" + def.id + "_run", 1f, noEvents, def.heroFrames);
            if (idle != null) { w.m_animationIdle = idle; w.m_animationIdleMagic = idle; combo.m_animationIdle = idle; }
            if (run != null) { w.m_animationRun = run; w.m_animationRunMagic = run; combo.m_animationRun = run; }

            var atks = new List<AttackData>();
            for (int k = 0; k < def.attacks.Count; k++)
            {
                var spec = def.attacks[k];
                var srcA = baseW.m_attacks[spec.src];
                var a = R.Clone(srcA);
                a.m_animationFront = HeroClip(srcA.m_animationFront, "ModW_" + def.id + "_" + k, spec.scale, spec.map, def.heroFrames);
                a.m_animAngles = new List<AttackDataAnimAngle>();
                int j = 0;
                foreach (var ang in srcA.m_animAngles)
                {
                    if (ang == null || ang.m_animation == null) continue;
                    a.m_animAngles.Add(new AttackDataAnimAngle
                    {
                        m_animation = HeroClip(ang.m_animation, "ModW_" + def.id + "_" + k + "_ang" + j++, spec.scale, spec.map, def.heroFrames),
                        m_angleRange = new MinMaxRange(ang.m_angleRange)
                    });
                }
                a.m_cooldown = spec.cooldown;
                atks.Add(a);
            }
            w.m_attacks = atks;
            w.m_attackDamageEffects = def.effects != null ? def.effects() : new List<DamageEffectData>();
            foreach (var e in w.m_attackDamageEffects)
                if (e.m_object == null) FurtherCore.Log.LogWarning(def.id + ": an effect template is missing");

            // no random magic or status rolls: the weapon's own mechanic is the point, and its name stays as written
            w.m_magic = new List<WeaponMagic>();
            w.m_magicLevelRange = new MinMaxRange(0f);
            w.m_magicChanceRange = new MinMaxRange(0f);
            w.m_specialAttacks = new List<SpecialAttackData>();
            w.m_chanceOfStatus = 0f;
            w.m_chanceOfOwnerStatus = 0f;
            Weapons[def.id] = w;

            if (!SellFrom(WeaponShopGroup, go, def.shopChance)) FurtherCore.Log.LogWarning("Weapon shop group not found");
            FurtherCore.Log.LogInfo("Weapon built: " + def.name + " (" + def.family + ", from " + def.baseWeapon + ", cost " + def.cost + ")");
            return w;
        }

        /// <summary>A vanilla SpawnGroup prefab by name (the shop groups), or null.</summary>
        public static SpawnGroup FindGroup(string name)
        {
            foreach (var g in Resources.FindObjectsOfTypeAll<SpawnGroup>())
                if (g.gameObject.name == name && !g.gameObject.scene.IsValid()) return g;
            return null;
        }

        /// <summary>Add <paramref name="go"/> to a shop group, copying the group's first entry. False if there is no such group.</summary>
        public static bool SellFrom(string group, GameObject go, float chance)
        {
            var g = FindGroup(group);
            if (g == null) return false;
            var items = R.Get<List<SpawnItem>>(g, "m_items");
            var like = items.Count > 0 ? items[0] : null;
            var it = like != null ? R.Clone(like) : new SpawnItem();
            it.m_object = go;
            it.m_chance = chance;
            items.Add(it);
            return true;
        }

        static exSpriteAnimClip Icon(string art, string anim)
        {
            if (art == null) return null;
            var sh = SpriteSheets.Get(art);
            if (sh == null) return null;
            if (!sh.Has(anim)) anim = sh.Has("Idle") ? "Idle" : anim;
            if (!sh.Has(anim)) return null;
            return new ClipBuilder(sh, anim, "Mod" + art + anim).Loop().Build();
        }

        /// <summary>
        /// A copy of a vanilla hero clip under a new name (the hero's exSpriteAnimation looks clips up by name, so a
        /// reused name would play the vanilla clip with vanilla events). Frame times are scaled, events move with them,
        /// AnimAttack / AnimMagic events are re-pointed through the map or dropped.
        /// </summary>
        static exSpriteAnimClip HeroClip(exSpriteAnimClip src, string name, float scale, Dictionary<string, int> map, HeroFrameMap frames)
        {
            if (src == null) return null;
            var c = UnityEngine.Object.Instantiate(src);
            c.name = name;
            var list = new List<exSpriteAnimClip.FrameInfo>();
            float len = 0f;
            foreach (var f in src.frameInfos)
            {
                exAtlas atlas = f.atlas; int index = f.index;
                if (frames != null) frames(f.atlas, f.index, out atlas, out index);
                list.Add(new exSpriteAnimClip.FrameInfo { atlas = atlas, index = index, length = f.length * scale, textureGUID = f.textureGUID });
                len += f.length * scale;
            }
            c.frameInfos = list;
            c.length = len;
            var evs = new List<exSpriteAnimClip.EventInfo>();
            foreach (var e in src.eventInfos)
            {
                string key = e.methodName == "AnimAttack" ? "a" + e.intParam : e.methodName == "AnimMagic" ? "m" + e.stringParam : null;
                int id = -1;
                if (key != null && (!map.TryGetValue(key, out id) || id < 0)) continue;
                var n = new exSpriteAnimClip.EventInfo
                {
                    time = Mathf.Min(e.time * scale, len), methodName = e.methodName, paramType = e.paramType, intParam = e.intParam,
                    floatParam = e.floatParam, stringParam = e.stringParam, objectParam = e.objectParam, boolParam = e.boolParam, msgOptions = e.msgOptions
                };
                if (key != null)
                {
                    n.methodName = "AnimAttack";
                    n.paramType = exSpriteAnimClip.EventInfo.ParamType.INT;
                    n.intParam = id;
                    n.stringParam = "";
                }
                evs.Add(n);
            }
            evs.Sort((x, y) => x.time.CompareTo(y.time));
            c.eventInfos = evs;
            SpriteSheets.Keep(c);
            return c;
        }
    }
}
