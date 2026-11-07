using System;
using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Heroes
{
    using CrawlFurther.Art;
    using CrawlFurther.Gods;
    using CrawlFurther.Items;
    using CrawlFurther.Util;

    /// <summary>
    /// Hero origins. After a player confirms a god they pick an origin; it is applied after every PlayerData.SetDeity, so
    /// it survives re-picks and never stacks (stats are set relative to the god's own, gear is cleared by SetDeity first).
    /// The first registered origin is the default for every player.
    /// </summary>
    public static class HeroClasses
    {
        /// <summary>Modifier source name for everything an origin adds.</summary>
        public const string MOD_SOURCE = "modorigin";

        /// <summary>Every origin in list order: the normal ones, then the silver and gold slots.</summary>
        public static readonly List<OriginDef> All = new List<OriginDef>();

        /// <summary>The player-built heroes behind the silver / gold origins; null: those slots act as plain origins.</summary>
        public static ICustomHeroes CustomHeroes;

        /// <summary>Chosen origin index per player id (default 0).</summary>
        public static readonly Dictionary<int, int> Chosen = new Dictionary<int, int>();

        static readonly Dictionary<string, exSpriteAnimClip> s_portraits = new Dictionary<string, exSpriteAnimClip>();
        static readonly Dictionary<string, UnityEngine.Object> s_cache = new Dictionary<string, UnityEngine.Object>();

        /// <summary>
        /// Add an origin to the list. Normal origins go in registration order before the silver and gold slots, which
        /// always stay the last two. Call it from your mod's start callback, before the god select is shown.
        /// </summary>
        public static void Register(OriginDef def)
        {
            if (def == null || All.Exists(d => d.id == def.id)) return;
            if (def.tier == SlotTier.Normal)
            {
                int at = All.FindIndex(d => d.tier != SlotTier.Normal);
                All.Insert(at < 0 ? All.Count : at, def);
            }
            else if (def.tier == SlotTier.Silver)
            {
                int at = All.FindIndex(d => d.tier == SlotTier.Gold);
                All.Insert(at < 0 ? All.Count : at, def);
            }
            else All.Add(def);
        }

        /// <summary>Number of normal origins (the silver and gold slots follow them).</summary>
        public static int RegularCount
        {
            get
            {
                int n = 0;
                foreach (var d in All) if (d.tier == SlotTier.Normal) n++;
                return n;
            }
        }

        /// <summary>What a player's origin actually grants: the def's Kind, or the player's own pick in a slot.</summary>
        public static OriginKind KindFor(OriginDef def, int playerId)
        {
            if (def == null) return OriginKind.Plain;
            if (def.tier == SlotTier.Normal) return def.Kind;
            return HeroClasses.CustomHeroes != null ? HeroClasses.CustomHeroes.KindOf(playerId, def.tier) : def.Kind;
        }

        /// <summary>The menu portrait of an origin for a player: the origin in that player's colours (sheet
        /// portraitArt + "_P1".."_P4"), or the player's own hero for a silver / gold slot. Looping, cached.</summary>
        public static exSpriteAnimClip PortraitClip(OriginDef def, int playerId)
        {
            if (def == null) return null;
            if (def.tier != SlotTier.Normal)
            {
                var c = HeroClasses.CustomHeroes != null ? HeroClasses.CustomHeroes.PortraitClip(playerId, def.tier) : null;
                if (c != null) return c;
            }
            int slot = HeroLooks.SlotOfId(playerId);
            string sid = def.tier == SlotTier.Normal ? def.portraitArt + "_P" + (slot + 1) : def.portraitArt;
            exSpriteAnimClip clip;
            if (s_portraits.TryGetValue(sid, out clip) && clip != null) return clip;
            var sh = SpriteSheets.Get(sid);
            if (sh == null || !sh.Has("Idle")) { sh = SpriteSheets.Get(def.portraitArt); sid = def.portraitArt; }
            if (sh == null || !sh.Has("Idle")) return null;
            clip = new ClipBuilder(sh, "Idle", "ModOrigin_" + sid).Loop().Build();
            s_portraits[sid] = clip;
            return clip;
        }

        /// <summary>A powerup that gives the hero a spell (a vanilla "Spell*" prefab, a spellbook artifact, or a mod spell).</summary>
        public static bool IsSpellPowerup(string name)
        {
            if (string.IsNullOrEmpty(name)) return false;
            return name.StartsWith("Spell", StringComparison.Ordinal) || name.StartsWith("ArtifactSpellbook", StringComparison.Ordinal)
                || name.StartsWith("ModSpell", StringComparison.Ordinal);
        }

        /// <summary>The origin a player has chosen (the first origin by default; null while none is registered).</summary>
        public static OriginDef For(PlayerData pd)
        {
            if (All.Count == 0) return null;
            int i;
            if (pd == null || !Chosen.TryGetValue(pd.Id, out i) || i < 0 || i >= All.Count) return All[0];
            return All[i];
        }

        /// <summary>Weapon prefab by name: mod weapons ("ModWeapon" + id) from ItemRegistry.Weapons, vanilla through FindPrefab.</summary>
        public static Weapon FindWeapon(string id)
        {
            if (string.IsNullOrEmpty(id)) return null;
            Weapon w;
            if (id.StartsWith("ModWeapon", StringComparison.Ordinal))
                return ItemRegistry.Weapons.TryGetValue(id.Substring(9), out w) ? w : null;
            return FindPrefab<Weapon>(id);
        }

        /// <summary>Spell powerup by name: mod spells ("Mod" + id) from ItemRegistry.Items, vanilla through FindPrefab.</summary>
        public static Powerup FindSpell(string id)
        {
            if (string.IsNullOrEmpty(id)) return null;
            Powerup p;
            if (id.StartsWith("Mod", StringComparison.Ordinal))
                return ItemRegistry.Items.TryGetValue(id.Substring(3), out p) ? p : null;
            return FindPrefab<Powerup>(id);
        }

        /// <summary>A vanilla prefab (a root object outside any scene) by name, cached.</summary>
        public static T FindPrefab<T>(string name) where T : Component
        {
            UnityEngine.Object o;
            if (s_cache.TryGetValue(name, out o) && o != null) return (T)o;
            foreach (var c in Resources.FindObjectsOfTypeAll<T>())
            {
                if (c.gameObject.name != name || c.transform.parent != null || c.gameObject.scene.IsValid()) continue;
                s_cache[name] = c;
                return c;
            }
            FurtherCore.Log.LogWarning("Origin: prefab not found " + name);
            return null;
        }

        /// <summary>Layer the player's origin on top of their god's starting kit (runs after PlayerData.SetDeity).</summary>
        public static void Apply(PlayerData pd)
        {
            if (pd == null) return;
            var def = For(pd);
            if (def == null) return;
            if (def.tier != SlotTier.Normal && HeroClasses.CustomHeroes != null) def = HeroClasses.CustomHeroes.Resolve(pd.Id, def.tier);
            var gd = pd.GameData;
            var playerObj = R.Get<GameObject>(pd, "m_playerObject");
            bool onInit = playerObj == null || !pd.IsHero;
            gd.RemoveModifiers(MOD_SOURCE);

            // stats are set relative to the god's own starting values, so re-applying never stacks and switching to
            // the default origin clears what the previous one changed
            if (onInit)
            {
                var deity = pd.GetDeity();
                SetStat(gd, deity, eHeroStatTypes.Vitality, def.vitality);
                SetStat(gd, deity, eHeroStatTypes.Strength, def.strength);
                SetStat(gd, deity, eHeroStatTypes.Dexterity, def.dexterity);
                if (!string.IsNullOrEmpty(def.weapon))
                {
                    var w = FindWeapon(def.weapon);
                    if (w != null) { var wd = new WeaponData(); wd.Init(w); gd.SetWeaponData(wd); }
                }
                if (def.gold != 0) gd.DebugIncrementLifeStat(PlayerStats.eStat.GoldEarned, def.gold);
            }
            foreach (var m in def.modifiers) gd.AddBaseModifier(MOD_SOURCE, m);
            foreach (var pn in def.powerups)
            {
                var pu = pn.StartsWith("Mod", StringComparison.Ordinal) ? FindSpell(pn) : FindPrefab<Powerup>(pn);
                if (pu != null && !gd.HasPowerup(pu)) Powerup.Collect(pu, pd, fromDeity: true);   // not counted as a library find
            }
        }

        static void SetStat(PlayerGameData gd, Deity deity, eHeroStatTypes t, int delta)
        {
            var data = Singleton<Constants>.Get.m_heroStats[(int)t];
            int target = data.m_starting + delta;
            if (deity != null)
                foreach (var hm in deity.GetHeroStatModifiers())
                    if (hm.m_type == t) target += hm.m_amount;
            int cur = Mathf.FloorToInt(gd.StatsGame.GetStat(data.m_playerStat));
            if (cur != target) gd.IncrementHeroStat(t, target - cur);
        }
    }

    [HarmonyPatch(typeof(PlayerData), "SetDeity", new[] { typeof(Deity) })]
    static class Patch_PlayerDataSetDeity
    {
        static void Postfix(PlayerData __instance)
        {
            try { HeroClasses.Apply(__instance); }
            catch (Exception e) { FurtherCore.Log.LogError("Origin apply failed: " + e); }
        }
    }
}
