using System;
using System.Collections;
using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Content.Gods
{
    using CrawlFurther.Gods;
    using CrawlFurther.Monsters;
    using CrawlFurther.UI;
    using CrawlFurther.Util;
    using CrawlFurther.Content.Ghosts;
    using CrawlFurther.Content.Gods.Jinx;
    using CrawlFurther.Content.Gods.Kaurn;
    using CrawlFurther.Content.Gods.Umbrael;
    using CrawlFurther.Content.Gods.Ysveld;
    using CrawlFurther.Content.Heroes;
    using CrawlFurther.Content.Secrets;

    // =====================================================================================================================
    // Custom gods: the silver (3 starters) and gold (4 starters) idols at the end of the god list. The player picks the
    // god whose PERK applies (any unlocked god, vanilla or mod) and every starter (any unlocked god's starters, no
    // duplicates). Each player slot gets its own Deity instance (no shared Deity asset is touched). Picks persist per
    // player slot in BepInEx/config/CrawlFurther.CustomGods.cfg.
    // =====================================================================================================================

    public static class CustomGod
    {
        public class Record
        {
            public int pid;
            public SlotTier tier;
            public string perk;
            public List<string> starters = new List<string>();
            public Deity deity;
            public Deity PerkGod { get { return Perk(perk); } }
            public Record Copy() { return new Record { pid = pid, tier = tier, perk = perk, starters = new List<string>(starters), deity = deity }; }
        }

        public class Starter { public Player p; public Deity god; }

        public const string FILE = "CrawlFurther.CustomGods.cfg";
        static readonly Dictionary<string, Record> s_rec = new Dictionary<string, Record>();
        static readonly Dictionary<Deity, Record> s_byDeity = new Dictionary<Deity, Record>();
        static Dictionary<string, string> s_cfg;

        public static int Slots(SlotTier t) { return t == SlotTier.Gold ? 4 : 3; }
        public static string TierName(SlotTier t) { return t == SlotTier.Gold ? "GOLD IDOL" : "SILVER IDOL"; }
        static bool s_inUse;
        /// <summary>True only while some active player's current deity is a custom one (refreshed whenever a deity is
        /// set or a player leaves): the perk hooks on every attack / state change / death bail out at once otherwise.</summary>
        public static bool InUse { get { return s_inUse; } }

        public static void RefreshInUse()
        {
            bool any = false;
            try
            {
                var all = SystemPlayers.GetPlayers();
                if (all != null)
                    foreach (var pd in all)
                        if (pd != null && pd.IsActive && pd.GameData != null && Of(pd.GetDeity()) != null) { any = true; break; }
            }
            catch { any = s_byDeity.Count > 0; }
            s_inUse = any;
        }

        /// <summary>Every unlocked, non-trial god (vanilla and mod), in god-list order.</summary>
        public static List<Deity> PerkGods()
        {
            var l = new List<Deity>();
            foreach (var d in SystemDeity.GetDeities())
                if (d != null && !d.GetIsTrial() && SystemDeity.GetUnlocked(d) && d.GetStartingMonsters() != null) l.Add(d);
            return l;
        }

        public static Deity Perk(string name)
        {
            foreach (var d in PerkGods()) if (d.GetName() == name) return d;
            return null;
        }

        /// <summary>Every starter of every unlocked god, grouped by god in god-list order, each monster once.</summary>
        public static List<Starter> Starters()
        {
            var l = new List<Starter>();
            var seen = new HashSet<GameObject>();
            foreach (var d in PerkGods())
                foreach (var go in d.GetStartingMonsters())
                    if (go != null && go.GetComponent<Player>() != null && seen.Add(go)) l.Add(new Starter { p = go.GetComponent<Player>(), god = d });
            return l;
        }

        // ------------------------------------------------------------------ the gold idol's secret starter
        /// <summary>The secret gold line's starter (GoldSecret.StarterId, built by GoldSecretPack), or null. It is offered
        /// only in a gold idol's last slot, as the very last entry, and belongs to no god.</summary>
        public static Player SecretStarter()
        {
            var id = GoldSecret.StarterId;
            if (string.IsNullOrEmpty(id)) return null;
            foreach (var p in MonsterFactory.Built.Values) if (p != null && p.gameObject.name == id) return p;
            return null;
        }

        public static bool IsSecret(string prefab) { return !string.IsNullOrEmpty(prefab) && prefab == GoldSecret.StarterId && SecretStarter() != null; }

        /// <summary>The secret may sit here: a gold idol's last slot only.</summary>
        public static bool SecretAllowed(SlotTier tier, int slot) { return tier == SlotTier.Gold && slot == Slots(tier) - 1; }

        /// <summary>The starters a slot offers: every normal starter, plus the secret as the very last entry in a gold
        /// idol's last slot.</summary>
        public static List<Starter> StartersFor(SlotTier tier, int slot)
        {
            var l = Starters();
            var sp = SecretAllowed(tier, slot) ? SecretStarter() : null;
            if (sp != null) l.Add(new Starter { p = sp, god = null });
            return l;
        }

        public static string GodName(Deity d)
        {
            if (d == null) return "";
            return d.GetName();
        }

        /// <summary>The god's perk line on one line.</summary>
        public static string PerkLine(Deity d)
        {
            if (d == null) return "";
            var t = (d.GetText() ?? "").Replace("\r", " ").Replace("\n", " ");
            while (t.Contains("  ")) t = t.Replace("  ", " ");
            return t.Trim();
        }

        // ------------------------------------------------------------------ records + persistence
        static string Key(int pid, SlotTier t) { return "P" + (pid + 1) + "." + (t == SlotTier.Gold ? "Gold" : "Silver"); }

        /// <summary>The player's stored picks for this slot (defaults filled in, invalid names replaced).</summary>
        public static Record Get(int pid, SlotTier tier)
        {
            Record r;
            string k = Key(pid, tier);
            if (!s_rec.TryGetValue(k, out r))
            {
                r = new Record { pid = pid, tier = tier };
                LoadCfg();
                string v;
                if (s_cfg.TryGetValue(k + ".Perk", out v)) r.perk = v;
                if (s_cfg.TryGetValue(k + ".Starters", out v))
                    foreach (var s in v.Split(',')) if (s.Trim().Length > 0) r.starters.Add(s.Trim());
                s_rec[k] = r;
            }
            Fix(r);
            return r;
        }

        /// <summary>Make a record valid: a known perk god, exactly Slots(tier) distinct known starters.</summary>
        public static void Fix(Record r)
        {
            var gods = PerkGods();
            if (gods.Count == 0) return;
            if (Perk(r.perk) == null) r.perk = gods[0].GetName();
            var all = Starters();
            var names = new HashSet<string>();
            foreach (var s in all) names.Add(s.p.gameObject.name);
            int n = Slots(r.tier);
            // the secret stays only where it may be: the last slot of a gold record
            bool secret = n > 0 && r.starters.Count >= n && SecretAllowed(r.tier, n - 1) && IsSecret(r.starters[n - 1]);
            int normal = secret ? n - 1 : n;
            var keep = new List<string>();
            for (int i = 0; i < r.starters.Count && i < (secret ? n - 1 : r.starters.Count); i++)
            {
                var s = r.starters[i];
                if (names.Contains(s) && !keep.Contains(s)) keep.Add(s);
            }
            if (keep.Count > normal) keep.RemoveRange(normal, keep.Count - normal);
            n = normal;
            // defaults: the perk god's own starters first, then the list in order
            var perk = Perk(r.perk);
            if (perk != null) foreach (var go in perk.GetStartingMonsters()) if (keep.Count < n && go != null && names.Contains(go.name) && !keep.Contains(go.name)) keep.Add(go.name);
            foreach (var s in all) if (keep.Count < n && !keep.Contains(s.p.gameObject.name)) keep.Add(s.p.gameObject.name);
            if (secret) keep.Add(GoldSecret.StarterId);
            r.starters = keep;
        }

        /// <summary>A record DONE may store: a known perk, Slots(tier) distinct known starters, the secret only in a
        /// gold idol's last slot.</summary>
        public static bool Valid(Record r)
        {
            if (r == null || Perk(r.perk) == null) return false;
            int n = Slots(r.tier);
            if (r.starters.Count != n) return false;
            var seen = new HashSet<string>();
            for (int i = 0; i < n; i++)
            {
                var s = r.starters[i];
                if (string.IsNullOrEmpty(s) || !seen.Add(s) || StarterByName(s) == null) return false;
                if (IsSecret(s) && !SecretAllowed(r.tier, i)) return false;
            }
            return true;
        }

        public static Player StarterByName(string name)
        {
            foreach (var s in Starters()) if (s.p.gameObject.name == name) return s.p;
            return IsSecret(name) ? SecretStarter() : null;
        }

        public static void Store(Record r)
        {
            Fix(r);
            var k = Key(r.pid, r.tier);
            Record cur;
            if (s_rec.TryGetValue(k, out cur)) { cur.perk = r.perk; cur.starters = new List<string>(r.starters); r = cur; }
            else s_rec[k] = r;
            LoadCfg();
            s_cfg[k + ".Perk"] = r.perk;
            s_cfg[k + ".Starters"] = string.Join(",", r.starters.ToArray());
            try
            {
                var sb = new System.Text.StringBuilder();
                sb.AppendLine("# Crawl: Further - each player slot's custom gods (silver and gold idol). Written by the mod.");
                sb.AppendLine("# Perk = the god whose perk applies; Starters = monster prefab names.");
                var keys = new List<string>(s_cfg.Keys); keys.Sort(StringComparer.Ordinal);
                foreach (var kk in keys) sb.AppendLine(kk + " = " + s_cfg[kk]);
                System.IO.File.WriteAllText(System.IO.Path.Combine(BepInEx.Paths.ConfigPath, FILE), sb.ToString());
            }
            catch (Exception e) { Plugin.Log.LogWarning("Custom gods: could not write " + FILE + ": " + e.Message); }
            DeityFor(r.pid, r.tier);
        }

        static void LoadCfg()
        {
            if (s_cfg != null) return;
            s_cfg = new Dictionary<string, string>();
            try
            {
                var path = System.IO.Path.Combine(BepInEx.Paths.ConfigPath, FILE);
                if (!System.IO.File.Exists(path)) return;
                foreach (var raw in System.IO.File.ReadAllLines(path))
                {
                    var line = raw.Trim();
                    if (line.Length == 0 || line[0] == '#' || line[0] == '[') continue;
                    int eq = line.IndexOf('=');
                    if (eq > 0) s_cfg[line.Substring(0, eq).Trim()] = line.Substring(eq + 1).Trim();
                }
            }
            catch (Exception e) { Plugin.Log.LogWarning("Custom gods: could not read " + FILE + ": " + e.Message); }
        }

        // ------------------------------------------------------------------ the Deity
        static readonly string[] CopyFields = { "m_modifiers", "m_heroStatModifiers", "m_gold", "m_startingWeapon", "m_startingPowerups",
            "m_soundSelected", "m_winHeroAnimation", "m_winText", "m_useLargeFodder", "m_weaponsForbidden", "m_spellsForbidden",
            "m_artifactsForbidden", "m_potionsForbidden" };

        /// <summary>
        /// This player's own Deity for the slot, rebuilt from the stored picks: the perk god's modifiers, hero stats,
        /// gold, starting kit and forbidden flags, the picked starters, the idol portrait. Never in the god list itself.
        /// </summary>
        public static Deity DeityFor(int pid, SlotTier tier)
        {
            var r = Get(pid, tier);
            var perk = r.PerkGod;
            if (r.deity == null) { r.deity = new Deity(); s_byDeity[r.deity] = r; }
            var d = r.deity;
            if (perk != null) foreach (var f in CopyFields) R.Set(d, f, R.Get<object>(perk, f));
            R.Set(d, "m_name", tier == SlotTier.Gold ? "Gold Idol" : "Silver Idol");
            R.Set(d, "m_text", "Perk of " + GodName(perk) + ": " + PerkLine(perk));
            R.Set(d, "m_textFlavour", tier == SlotTier.Gold ? "A crown of your own\nmaking. It answers you." : "Carved by your hand,\nworshipped by you alone.");
            R.Set(d, "m_neverChooseRandomly", true);
            R.Set(d, "m_isTrial", false);
            var clip = SlotArt.Clip(tier == SlotTier.Gold ? "DeityGoldIdol" : "DeitySilverIdol", "Idle");
            R.Set(d, "m_portrait", SlotGods.Portrait(tier, perk, clip) ?? (perk != null ? perk.GetPortraitAnim() : null));
            var mons = new List<GameObject>();
            foreach (var n in r.starters) { var p = StarterByName(n); if (p != null) mons.Add(p.gameObject); }
            R.Set(d, "m_startingMonsters", mons.ToArray());
            return d;
        }

        /// <summary>The record behind a custom Deity (null for every real god).</summary>
        public static Record Of(Deity d)
        {
            Record r;
            return d != null && s_byDeity.TryGetValue(d, out r) ? r : null;
        }

        public static bool IsCustom(Deity d) { return Of(d) != null; }

        // ------------------------------------------------------------------ perks that live on the monsters
        static readonly Dictionary<Deity, GameObject> s_deathPerk = new Dictionary<Deity, GameObject>();

        /// <summary>A mod god's on-death perk object (fire pool, brine, ice, bones, seeds, larva, rod): the "Mod" death
        /// spawn every one of its starters carries. Null for vanilla gods and for gods whose perk is not a death spawn.</summary>
        public static GameObject DeathPerk(Deity god)
        {
            if (god == null) return null;
            GameObject fx;
            if (s_deathPerk.TryGetValue(god, out fx)) return fx;
            fx = null;
            HashSet<GameObject> common = null;
            foreach (var go in god.GetStartingMonsters())
            {
                var p = go != null ? go.GetComponent<Player>() : null;
                if (p == null) continue;
                var set = new HashSet<GameObject>();
                var arr = R.Get<DamageEffectData[]>(p, "m_spawnOnDeath");
                if (arr != null) foreach (var e in arr) if (e != null && e.m_object != null && e.m_object.name.StartsWith("Mod")) set.Add(e.m_object);
                if (common == null) common = set; else common.IntersectWith(set);
            }
            if (common != null) foreach (var g in common) { fx = g; break; }
            s_deathPerk[god] = fx;
            return fx;
        }

        static HashSet<GameObject> s_allDeathPerks;
        /// <summary>Every mod god's on-death perk object (each starter's own god's perk, to be swapped out).</summary>
        public static HashSet<GameObject> AllDeathPerks
        {
            get
            {
                if (s_allDeathPerks != null) return s_allDeathPerks;
                var set = new HashSet<GameObject>();
                foreach (var d in SystemDeity.GetDeities())
                    if (d != null && !d.GetIsTrial() && DeityFactory.BuiltNames.Contains(d.GetName()))
                    {
                        var fx = DeathPerk(d);
                        if (fx != null) set.Add(fx);
                    }
                s_allDeathPerks = set;
                return set;
            }
        }

        /// <summary>Is <paramref name="p"/> a monster of a player whose custom god's perk is NOT <paramref name="god"/>?
        /// (Then that god's perk, which the monster carries from its own tree, does not apply.)</summary>
        public static bool PerkSwappedAway(Player p, string god)
        {
            if (!s_inUse || p == null) return false;
            var pd = CustomPerks.Owner(p);
            var rec = pd != null && !pd.IsHero ? Of(pd.GetDeity()) : null;
            return rec != null && rec.perk != god;
        }

        public static void SelfCheck(Action<string> bad)
        {
            // the checks build Deities for P1-P4: put the tables back as they were afterwards
            var before = new HashSet<Deity>(s_byDeity.Keys);
            var hadDeity = new Dictionary<string, bool>();
            foreach (var kv in s_rec) hadDeity[kv.Key] = kv.Value.deity != null;
            try { SelfCheckBody(bad); }
            finally
            {
                var added = new List<Deity>();
                foreach (var d in s_byDeity.Keys) if (!before.Contains(d)) added.Add(d);
                foreach (var d in added) s_byDeity.Remove(d);
                foreach (var kv in s_rec)
                {
                    bool had;
                    if (!(hadDeity.TryGetValue(kv.Key, out had) && had)) kv.Value.deity = null;
                }
                RefreshInUse();
            }
        }

        static void SelfCheckBody(Action<string> bad)
        {
            var gods = PerkGods();
            if (gods.Count < 2) bad("custom god: only " + gods.Count + " perk gods");
            var st = Starters();
            if (st.Count < 4) bad("custom god: only " + st.Count + " starters");
            foreach (var g in gods)
                if (DeityFactory.BuiltNames.Contains(g.GetName()) && DeathPerk(g) == null && g.GetName() != "Umbrael" && g.GetName() != "Jinx")
                    bad("custom god: no death perk found for " + g.GetName());
            for (int pid = 0; pid < 4; pid++)
                foreach (var t in new[] { SlotTier.Silver, SlotTier.Gold })
                {
                    var r = Get(pid, t);
                    if (r.starters.Count != Slots(t)) bad("custom god " + Key(pid, t) + ": " + r.starters.Count + " starters");
                    var d = DeityFor(pid, t);
                    if (d.GetStartingMonsters().Length != Slots(t)) bad("custom god " + Key(pid, t) + ": deity has " + d.GetStartingMonsters().Length);
                    if (SystemDeity.GetDeities().Contains(d)) bad("custom god leaked into the god list");
                }
            if (DeityFor(0, SlotTier.Silver) == DeityFor(1, SlotTier.Silver)) bad("custom god: players share a Deity");
            // the secret gold line: gold idol, last slot, last entry; never anywhere else
            if (st.Count < 4 || gods.Count == 0) return;
            var sp = SecretStarter();
            if (sp == null) { bad("custom god: the secret gold starter (" + (GoldSecret.StarterId ?? "null") + ") is not built"); return; }
            string sid = sp.gameObject.name;
            foreach (var t in new[] { SlotTier.Silver, SlotTier.Gold })
                for (int k = 0; k < Slots(t); k++)
                {
                    var l = StartersFor(t, k);
                    int at = l.FindIndex(x => x.p == sp);
                    bool want = t == SlotTier.Gold && k == Slots(t) - 1;
                    if (want && at != l.Count - 1) bad("custom god: the secret is not the last entry of the gold idol's last slot");
                    if (!want && at >= 0) bad("custom god: the secret is offered in " + t + " slot " + (k + 1));
                }
            foreach (var x in Starters()) if (x.p == sp) bad("custom god: the secret is in the normal starter list (bots and other slots would see it)");
            var gold = new Record { pid = -1, tier = SlotTier.Gold, perk = gods.Count > 0 ? gods[0].GetName() : null, starters = new List<string> { st[0].p.gameObject.name, st[1].p.gameObject.name, st[2].p.gameObject.name, sid } };
            Fix(gold);
            if (gold.starters.Count != 4 || gold.starters[3] != sid) bad("custom god: Fix dropped the secret from the gold idol's last slot");
            if (!Valid(gold)) bad("custom god: a gold idol with the secret last is not valid");
            var early = new Record { pid = -1, tier = SlotTier.Gold, perk = gold.perk, starters = new List<string> { sid, st[1].p.gameObject.name, st[2].p.gameObject.name, st[3].p.gameObject.name } };
            if (Valid(early)) bad("custom god: the secret is valid in slot 1");
            Fix(early);
            if (early.starters.Contains(sid)) bad("custom god: Fix kept the secret outside the last slot");
            var silver = new Record { pid = -1, tier = SlotTier.Silver, perk = gold.perk, starters = new List<string> { st[0].p.gameObject.name, st[1].p.gameObject.name, sid } };
            if (Valid(silver)) bad("custom god: the secret is valid on a silver idol");
            Fix(silver);
            if (silver.starters.Contains(sid)) bad("custom god: Fix kept the secret on a silver idol");
            if (StarterByName(sid) != sp) bad("custom god: StarterByName does not find the secret");
        }
    }

    // =================================================================================================================
    //  Runtime: four starters, and the perks that live on monsters
    // =================================================================================================================

    /// <summary>The spawn order is a ShuffledIndex sized once (3) in the constructor: resize it with the starter list, or
    /// a gold idol's 4th monster never spawns (and going back to 3 would index past the end).</summary>
    [HarmonyPatch(typeof(PlayerGameData), "SetStartingMonsters")]
    static class Patch_StartersShuffle
    {
        static void Postfix(PlayerGameData __instance, GameObject[] monsters)
        {
            try
            {
                if (monsters == null) return;
                var si = R.Get<ShuffledIndex>(__instance, "m_shuffledMonsterId");
                var ids = si != null ? R.Get<int[]>(si, "m_ids") : null;
                if (ids == null || ids.Length != monsters.Length) R.Set(__instance, "m_shuffledMonsterId", new ShuffledIndex(monsters.Length));
            }
            catch (Exception e) { Plugin.Log.LogWarning("Starter shuffle resize: " + e.Message); }
        }
    }

    /// <summary>
    /// A custom god's perk replaces the starters' own: for a monster of a custom-god player, every mod god's on-death
    /// perk object is taken out of its death spawns for this death, and the chosen perk god's one is put in (fire pool,
    /// brine, ice, bones, seed, larva, rod). The monster's own kit (attacks, specials, passives) is untouched. The
    /// array is swapped only for the length of OnKilled (pooled bodies are shared by every player).
    /// </summary>
    [HarmonyPatch(typeof(Player), "OnKilled")]
    static class Patch_CustomPerkDeath
    {
        static readonly AccessTools.FieldRef<Player, bool> s_hero = AccessTools.FieldRefAccess<Player, bool>("m_isHero");
        static readonly AccessTools.FieldRef<Player, Player.ePlayerState> s_state = AccessTools.FieldRefAccess<Player, Player.ePlayerState>("m_state");
        static readonly AccessTools.FieldRef<Player, DamageEffectData[]> s_spawn = AccessTools.FieldRefAccess<Player, DamageEffectData[]>("m_spawnOnDeath");
        static readonly Dictionary<string, DamageEffectData> s_data = new Dictionary<string, DamageEffectData>();

        static void Prefix(Player __instance, out DamageEffectData[] __state)
        {
            __state = null;
            if (!CustomGod.InUse || __instance == null) return;
            try
            {
                if (s_hero(__instance) || s_state(__instance) == Player.ePlayerState.Dead) return;
                var pd = CustomPerks.Owner(__instance);
                var rec = pd != null && !pd.IsHero ? CustomGod.Of(pd.GetDeity()) : null;
                if (rec == null) return;
                var keep = CustomGod.DeathPerk(rec.PerkGod);
                var all = CustomGod.AllDeathPerks;
                var arr = s_spawn(__instance) ?? new DamageEffectData[0];
                var list = new List<DamageEffectData>(arr.Length + 1);
                bool changed = false, has = false;
                foreach (var e in arr)
                {
                    var o = e != null ? e.m_object : null;
                    if (o != null && all.Contains(o) && o != keep) { changed = true; continue; }   // another god's perk
                    if (o != null && o == keep) has = true;
                    list.Add(e);
                }
                if (keep != null && !has) { list.Add(Data(__instance, keep)); changed = true; }
                if (!changed) return;
                __state = arr;
                s_spawn(__instance) = list.ToArray();
            }
            catch (Exception e) { CustomPerks.Warn("death", e); }
        }

        static void Postfix(Player __instance, DamageEffectData[] __state)
        {
            if (__state != null && __instance != null) s_spawn(__instance) = __state;
        }

        static DamageEffectData Data(Player p, GameObject fx)
        {
            string key = ModUtil.PrefabName(p.gameObject) + "|" + fx.name;
            DamageEffectData d;
            if (s_data.TryGetValue(key, out d)) return d;
            var spr = p.GetComponent<exSprite>();
            float fy = spr != null ? spr.offset.y + 2f : 0f;   // at the feet, as Strike.DeathAtFeet places the gods' own
            var node = R.Get<Vector2>(p, "m_attackSpawnNode");
            d = new DamageEffectData
            {
                m_object = fx, m_attach = false, m_destroyOnAnimEnd = false,
                m_offsetX = new MinMaxRange(0f), m_offsetY = new MinMaxRange(fy - node.y), m_angle = new MinMaxRange(0f),
                m_scaleX = new MinMaxRange(1f), m_scaleY = new MinMaxRange(1f), m_spawnDelay = new MinMaxRange(0f)
            };
            s_data[key] = d;
            return d;
        }
    }

    /// <summary>Umbrael starters under another custom perk: no Twice Struck echo.</summary>
    [HarmonyPatch(typeof(ModMonster), "QueueEcho")]
    static class Patch_CustomPerkNoEcho
    {
        static bool Prefix(ModMonster __instance)
        {
            if (!CustomGod.InUse) return true;
            try { return !CustomGod.PerkSwappedAway(__instance.GetComponent<Player>(), "Umbrael"); } catch { return true; }
        }
    }

    /// <summary>Jinx starters under another custom perk: no Wild Card.</summary>
    [HarmonyPatch(typeof(JinxMonster), "ModWildCard")]
    static class Patch_CustomPerkNoWildCard
    {
        static bool Prefix(JinxMonster __instance)
        {
            if (!CustomGod.InUse) return true;
            try { return !CustomGod.PerkSwappedAway(__instance.GetComponent<Player>(), "Jinx"); } catch { return true; }
        }
    }

    /// <summary>Ysveld starters under another custom perk: no extra speed on ice.</summary>
    [HarmonyPatch(typeof(YsvMonster), "Update")]
    static class Patch_CustomPerkNoIceSpeed
    {
        static bool Prefix(YsvMonster __instance)
        {
            if (!CustomGod.InUse) return true;
            try { return !CustomGod.PerkSwappedAway(__instance.GetComponent<Player>(), "Ysveld"); } catch { return true; }
        }
    }

    /// <summary>Kaurn starters under another custom perk: their bodies don't start conduction arcs (Kaurn's perk) for
    /// this rescan. They are taken out of the unit list for the scan and put back after it.</summary>
    [HarmonyPatch(typeof(KaurnConduction), "Rescan")]
    static class Patch_CustomPerkNoArcs
    {
        static void Prefix(out List<KaurnUnit> __state)
        {
            __state = null;
            if (!CustomGod.InUse) return;
            try
            {
                for (int i = KaurnUnit.All.Count - 1; i >= 0; i--)
                {
                    var u = KaurnUnit.All[i];
                    if (u != null && CustomGod.PerkSwappedAway(u.GetComponent<Player>(), "Kaurn"))
                    {
                        (__state ?? (__state = new List<KaurnUnit>())).Add(u);
                        KaurnUnit.All.RemoveAt(i);
                    }
                }
            }
            catch (Exception e) { CustomPerks.Warn("arcs", e); }
        }

        static void Postfix(List<KaurnUnit> __state)
        {
            if (__state == null) return;
            foreach (var u in __state) if (u != null && u.isActiveAndEnabled && !KaurnUnit.All.Contains(u)) KaurnUnit.All.Add(u);
        }
    }

    /// <summary>Keep CustomGod.InUse current: a player's deity changed, or a player left.</summary>
    [HarmonyPatch(typeof(PlayerData), "SetDeity", new[] { typeof(Deity) })]
    static class Patch_CustomGodInUse
    {
        static void Postfix() { CustomGod.RefreshInUse(); }
    }

    [HarmonyPatch(typeof(PlayerData), "Unassign")]
    static class Patch_CustomGodInUseLeave
    {
        static void Postfix() { CustomGod.RefreshInUse(); }
    }

    /// <summary>Umbrael's perk on a custom god: each basic attack has a half-strength shadow repeat 0.6 s later.</summary>
    [HarmonyPatch(typeof(Attacks), "SpawnEffect", new[] { typeof(DamageEffectData), typeof(int) })]
    [HarmonyAfter(FurtherCore.GUID)]   // after Core's own echo postfix, as in 0.10.0
    static class Patch_CustomPerkEcho
    {
        static readonly AccessTools.FieldRef<Attacks, IAttacksOwner> s_owner = AccessTools.FieldRefAccess<Attacks, IAttacksOwner>("m_owner");
        static readonly AccessTools.FieldRef<Player, Player.ePlayerState> s_state = AccessTools.FieldRefAccess<Player, Player.ePlayerState>("m_state");

        static void Postfix(Attacks __instance, DamageEffectData effectData, GameObject __result)
        {
            if (!CustomGod.InUse || __result == null || effectData == null || effectData.m_object == null) return;
            try
            {
                var p = s_owner(__instance) as Player;
                if (p == null || s_state(p) != Player.ePlayerState.Attack) return;
                var pd = CustomPerks.Owner(p);
                var rec = pd != null && !pd.IsHero ? CustomGod.Of(pd.GetDeity()) : null;
                if (rec == null || rec.perk != "Umbrael") return;
                var mm = p.GetComponent<ModMonster>();
                if (mm != null && mm.Traits.echo) return;   // Umbrael's own monsters already echo
                if (effectData.m_object.GetComponent<DamageEffect>() == null) return;
                CustomPerks.Echo(p, effectData.m_object, __result);
            }
            catch (Exception e) { CustomPerks.Warn("echo", e); }
        }
    }

    /// <summary>Jinx's perk on a custom god: every special flips a Wild Card over the monster, a random boon.</summary>
    [HarmonyPatch(typeof(Player), "SetState", new[] { typeof(Player.ePlayerState) })]
    static class Patch_CustomPerkWildCard
    {
        static void Postfix(Player __instance, Player.ePlayerState state)
        {
            if (state != Player.ePlayerState.AttackSpecial || !CustomGod.InUse) return;
            try
            {
                var pd = CustomPerks.Owner(__instance);
                var rec = pd != null && !pd.IsHero ? CustomGod.Of(pd.GetDeity()) : null;
                if (rec == null || rec.perk != "Jinx") return;
                var mm = __instance.GetComponent<ModMonster>();
                if (mm != null && mm.Traits is JinxTraits) return;
                CustomPerks.WildCard(__instance, pd);
            }
            catch (Exception e) { CustomPerks.Warn("wild card", e); }
        }
    }

    public class CustomPerks : MonoBehaviour
    {
        static CustomPerks s_inst;
        static readonly HashSet<string> s_warned = new HashSet<string>();
        static readonly Dictionary<GameObject, GameObject> s_echo = new Dictionary<GameObject, GameObject>();
        static readonly Dictionary<Player, float> s_lastEcho = new Dictionary<Player, float>();
        const float EchoDelay = 0.6f;

        public static void Warn(string what, Exception e) { if (s_warned.Add(what)) Plugin.Log.LogWarning("Custom god perk (" + what + "): " + e.Message); }

        static CustomPerks I
        {
            get
            {
                if (s_inst == null)
                {
                    var go = new GameObject("CrawlFurther.CustomPerks");
                    DontDestroyOnLoad(go);
                    s_inst = go.AddComponent<CustomPerks>();
                }
                return s_inst;
            }
        }

        /// <summary>The player a monster belongs to: its controller, or whoever spawned it.</summary>
        public static PlayerData Owner(Player p)
        {
            if (p == null) return null;
            return R.Get<PlayerData>(p, "m_playerData") ?? R.Get<PlayerData>(p, "m_spawner");
        }

        public static void Echo(Player p, GameObject template, GameObject spawned)
        {
            float last;
            if (s_lastEcho.TryGetValue(p, out last) && Time.time - last < 0.25f) return;
            s_lastEcho[p] = Time.time;
            GameObject echo;
            if ((echo = FxKit.FindEcho(template)) == null && !s_echo.TryGetValue(template, out echo))
            {
                echo = FxKit.EchoOf(template, 0.5f);
                s_echo[template] = echo;
            }
            if (echo == null) return;
            var spr = p.GetComponent<exSprite>();
            if (spr != null) AfterimageFx.Spawn(spr, p.transform.position, EchoDelay + 0.15f);
            if (UmbraelFx.EchoSmear != null) SystemPool.Spawn(UmbraelFx.EchoSmear, p.transform.position);
            I.StartCoroutine(I.EchoLater(echo, spawned.transform.position, spawned.transform.rotation, spawned.transform.lossyScale, FxFactory.SourceOf(spawned)));
        }

        IEnumerator EchoLater(GameObject tmpl, Vector3 pos, Quaternion rot, Vector3 scale, DamageSource src)
        {
            yield return new WaitForSeconds(EchoDelay);
            if (tmpl == null) yield break;
            var go = SystemPool.SpawnBegin(tmpl, pos, rot);
            if (go == null) yield break;
            go.transform.localScale = scale;
            if (src != null)
                go.SendMessage(Constants.MSG_SETSPAWNER, ModUtil.HandOn(src, go), SendMessageOptions.DontRequireReceiver);
            SystemPool.SpawnFinalize(go);
        }

        static readonly Dictionary<PlayerData, int> s_buffs = new Dictionary<PlayerData, int>();

        /// <summary>Hearts heal 1, Spades 1.5x damage for 3 s, Diamonds 1.3x attack speed for 3 s, Clubs 1.4x run speed for 2.5 s.</summary>
        public static void WildCard(Player p, PlayerData pd)
        {
            int suit = UnityEngine.Random.Range(0, 4);
            if (JinxFx.WildCard != null)
            {
                var fx = SystemPool.Spawn(JinxFx.WildCard, (Vector2)p.transform.position + new Vector2(0f, 18f));
                var anim = fx != null ? fx.GetComponent<exSpriteAnimation>() : null;
                if (anim != null && JinxFx.Suits != null && JinxFx.Suits.Length > suit && JinxFx.Suits[suit] != null)
                    I.StartCoroutine(ShowSuit(anim, JinxFx.Suits[suit]));
            }
            switch (suit)
            {
                case 0:
                    var h = p.GetComponent<Health>();
                    if (h != null) { h.Heal(1f); ModInd.Heal(p.gameObject); }
                    break;
                case 1: I.StartCoroutine(I.Buff(p, pd, PlayerModifier.eType.MonsterDamage, 1.5f, 3f, true)); break;
                case 2: I.StartCoroutine(I.Buff(p, pd, PlayerModifier.eType.MonsterAttackAnimSpeed, 1.3f, 3f, true)); break;
                default: I.StartCoroutine(I.Buff(p, pd, PlayerModifier.eType.MonsterSpeed, 1.4f, 2.5f, false)); break;
            }
        }

        static IEnumerator ShowSuit(exSpriteAnimation anim, exSpriteAnimClip face)
        {
            yield return new WaitForSeconds(0.32f);
            if (anim != null && anim.isActiveAndEnabled) anim.Play(face);
        }

        IEnumerator Buff(Player p, PlayerData pd, PlayerModifier.eType t, float mult, float time, bool aura)
        {
            string src = "modidolwild" + (int)t;
            int n; s_buffs.TryGetValue(pd, out n); s_buffs[pd] = n + 1;
            pd.GameData.RemoveModifiers(src);
            pd.GameData.AddBaseModifier(src, new PlayerModifier { m_modify = t, m_type = ValueModifier.eModifierType.Multiply, m_value = mult });
            GameObject fx = null;
            if (aura && JinxFx.SurgeAura != null && p != null) fx = ModAttach.Spawn(JinxFx.SurgeAura, p.gameObject, Vector2.zero, 0.01f);
            yield return new WaitForSeconds(time);
            pd.GameData.RemoveModifiers(src);
            if (fx != null) fx.Despawn();
        }
    }

    // =================================================================================================================
    //  The god list's silver and gold slots
    // =================================================================================================================

    /// <summary>
    /// Two entries appended to every player's god list after vanilla built it (so they are always the last two, after
    /// every god and the trials entry, whatever is added later). Hovering one shows the idol, its perk / lock text and
    /// the picked starters (four boxes for gold); confirming an open one opens the custom-god editor, then the origin
    /// page; confirming a locked one rattles the lock.
    /// </summary>
    public class GodSlots : MonoBehaviour
    {
        MenuDeitySelectPlayer m_panel;
        int m_silver = -1, m_gold = -1;
        SlotTier m_shown = SlotTier.Normal;
        bool m_dirty = true;
        GameObject m_box4;
        Vector3[] m_boxPos;
        bool m_four;
        int m_frame;
        public SlotTier Confirmed { get; private set; }
        // the panel's parts, read once (PanelUpdate runs every frame for every panel)
        MenuTextMenu m_list, m_trials;
        GameObject m_arrowL, m_arrowR;
        int m_pid = -1;

        public static GodSlots Of(MenuDeitySelectPlayer panel) { return panel != null ? panel.GetComponent<GodSlots>() : null; }

        /// <summary>From the god-list layout patch, after vanilla Start filled the list.</summary>
        public static void AddItems(MenuDeitySelectPlayer panel, MenuTextMenu menu)
        {
            if (SlotEditors.God == null) SlotEditors.God = CustomGodEditor.For;
            if (SlotEditors.Hero == null) SlotEditors.Hero = HeroEditor.For;
            if (SlotEditors.Ghost == null) SlotEditors.Ghost = GhostEditor.For;
            UnlockToast.Ensure();
            var gs = panel.GetComponent<GodSlots>() ?? panel.gameObject.AddComponent<GodSlots>();
            if (gs.m_gold >= 0) return;
            gs.m_panel = panel;
            gs.m_list = menu;
            gs.m_trials = R.Get<MenuTextMenu>(panel, "m_menuTrials");
            gs.m_arrowL = R.Get<GameObject>(panel, "m_arrowL");
            gs.m_arrowR = R.Get<GameObject>(panel, "m_arrowR");
            gs.m_pid = R.Get<int>(panel, "m_playerId");
            var prefab = R.Get<MenuItemImage>(panel, "m_prefabMenuItem");
            foreach (var t in new[] { SlotTier.Silver, SlotTier.Gold })
            {
                var item = menu.AddItem(new MenuTextMenuItemData { m_enabled = true, m_prefabMenuItem = prefab,
                                                                    m_message = t == SlotTier.Gold ? "MsgModGodGold" : "MsgModGodSilver" }) as MenuItemImage;
                if (item != null) item.SetAnim(SlotArt.TierPip(t, Unlocks.IsUnlocked(Unlocks.IdFor("God", t))));
            }
            int n = menu.GetItemCount();
            gs.m_silver = n - 2; gs.m_gold = n - 1;
        }

        public static void HideExtras(MenuDeitySelectPlayer panel)
        {
            var gs = Of(panel);
            if (gs == null) return;
            gs.Layout(false);
            gs.m_shown = SlotTier.Normal;
            gs.m_dirty = true;
            SlotLock.Show(panel, false);
        }

        public static void Invalidate(MenuDeitySelectPlayer panel)
        {
            var gs = Of(panel);
            if (gs != null) { gs.m_dirty = true; gs.m_shown = SlotTier.Normal; }
        }

        /// <summary>The slot the god list has selected (Normal for every god / random / trials entry).</summary>
        public static SlotTier Selected(MenuDeitySelectPlayer panel)
        {
            var gs = Of(panel);
            if (gs == null || gs.m_gold < 0) return SlotTier.Normal;
            var trials = R.Get<MenuTextMenu>(panel, "m_menuTrials");
            if (trials != null && trials.gameObject.activeSelf) return SlotTier.Normal;
            int sel = R.Get<MenuTextMenu>(panel, "m_menu").GetSelectedId();
            return sel == gs.m_gold ? SlotTier.Gold : sel == gs.m_silver ? SlotTier.Silver : SlotTier.Normal;
        }

        int PlayerId { get { return m_pid; } }

        static System.Reflection.MethodInfo s_setTrials;

        /// <summary>The panel's Update prefix: true lets vanilla run.</summary>
        public static bool PanelUpdate(MenuDeitySelectPlayer panel)
        {
            var gs = Of(panel);
            if (gs == null || gs.m_gold < 0 || gs.m_list == null) return true;
            var menu = gs.m_list;
            var trials = gs.m_trials;
            if (trials != null && trials.gameObject.activeSelf) { gs.Leave(); return true; }
            int sel = menu.GetSelectedId();
            SlotTier t = sel == gs.m_gold ? SlotTier.Gold : sel == gs.m_silver ? SlotTier.Silver : SlotTier.Normal;
            if (t == SlotTier.Normal)
            {
                gs.Leave();
                if (sel != gs.m_silver - 1) return true;
                // the trials entry is no longer the last item: vanilla would read it as a god
                if (s_setTrials == null) s_setTrials = AccessTools.Method(typeof(MenuDeitySelectPlayer), "SetTrialsDeity");
                s_setTrials.Invoke(panel, null);
                gs.Arrows(menu);
                return false;
            }
            if (gs.m_dirty || gs.m_shown != t) gs.Show(t);
            gs.Arrows(menu);
            return false;
        }

        void Arrows(MenuTextMenu menu)
        {
            if (m_arrowL != null) m_arrowL.SetActive(menu.HasPrevColumn());
            if (m_arrowR != null) m_arrowR.SetActive(menu.HasNextColumn());
        }

        void Leave()
        {
            if (m_shown == SlotTier.Normal && !m_four) return;
            m_shown = SlotTier.Normal;
            Layout(false);
            SlotLock.Show(m_panel, false);
            SlotArt.ResetName(R.Get<TextMesh>(m_panel, "m_name"));
        }

        void Show(SlotTier t)
        {
            m_shown = t;
            m_dirty = false;
            // vanilla redraws whatever is selected next
            R.Set(m_panel, "m_deity", null);
            var tf = AccessTools.Field(typeof(MenuDeitySelectPlayer), "m_selectedItemType");
            tf.SetValue(m_panel, Enum.ToObject(tf.FieldType, 0));
            bool open = Unlocks.IsUnlocked(Unlocks.IdFor("God", t));
            var portrait = R.Get<exSpriteAnimation>(m_panel, "m_portrait");
            string sheet = t == SlotTier.Gold ? "DeityGoldIdol" : "DeitySilverIdol";
            var clip = open ? SlotGods.Portrait(t, CustomGod.Get(PlayerId, t).PerkGod, SlotArt.Clip(sheet, "Idle")) : SlotArt.Clip(sheet, "Locked");
            if (portrait != null && clip != null)
            {
                var g = portrait.GetComponent<Glitch>();
                if (g != null) g.enabled = false;
                if (portrait.GetAnimation(clip.name) == null) portrait.AddAnimation(clip);
                portrait.Play(clip.name);
            }
            SlotLock.Show(m_panel, !open);
            var name = R.Get<TextMesh>(m_panel, "m_name");
            SlotArt.FitName(name, CustomGod.TierName(t));
            var text = R.Get<GUIText>(m_panel, "m_text");
            var flav = R.Get<GUIText>(m_panel, "m_textFlavour");
            var pd = SystemPlayers.GetPlayer(PlayerId);
            var c = Unlocks.Find(Unlocks.IdFor("God", t));
            Layout(t == SlotTier.Gold);
            var mons = R.Get<exSprite[]>(m_panel, "m_monsters");
            if (!open)
            {
                if (text != null) text.SetText(c.text + "  " + Unlocks.ProgressShort(c.id));
                if (flav != null) flav.SetText("");
                PanelText.Fit(text);
                for (int i = 0; i < 4; i++) { var s = Img(mons, i); if (s != null) s.gameObject.SetActive(false); }
                return;
            }
            var rec = CustomGod.Get(PlayerId, t);
            if (text != null) text.SetText("Any " + CustomGod.Slots(t) + " starters, only " + CustomGod.GodName(rec.PerkGod) + "'s perk");
            var d = CustomGod.DeityFor(PlayerId, t);
            if (flav != null) flav.SetText(d.GetTextFlavour());
            PanelText.Fit(text); PanelText.Fit(flav);
            for (int i = 0; i < 4; i++)
            {
                var s = Img(mons, i);
                if (s == null) continue;
                var p = i < rec.starters.Count ? CustomGod.StarterByName(rec.starters[i]) : null;
                var clipper = s.GetComponent<exClipping>();
                if (p == null) { s.gameObject.SetActive(false); continue; }
                if (clipper != null) clipper.RemovePlane(s);
                s.gameObject.SetActive(true);
                p.SetupPortrait(s);
                if (clipper != null) clipper.AddPlane(s);
            }
            if (pd != null && !pd.IsBot && pd.GetDeity() != d) pd.SetDeity(d);   // live, like hovering a god
        }

        exSprite Img(exSprite[] mons, int i)
        {
            if (i < 3) return mons != null && i < mons.Length ? mons[i] : null;
            if (!m_four || m_box4 == null) return null;
            foreach (var s in m_box4.GetComponentsInChildren<exSprite>(true)) if (s.GetComponent<exClipping>() != null) return s;
            return null;
        }

        /// <summary>Three boxes at -11 / 0 / 11 (vanilla), or four at -16.5 / -5.5 / 5.5 / 16.5 for the gold idol.</summary>
        void Layout(bool four)
        {
            var mons = R.Get<exSprite[]>(m_panel, "m_monsters");
            if (mons == null || mons.Length < 3 || mons[2] == null) return;
            if (m_boxPos == null)
            {
                m_boxPos = new Vector3[3];
                for (int i = 0; i < 3; i++) m_boxPos[i] = mons[i].transform.parent.localPosition;
            }
            if (four && m_box4 == null)
            {
                var src = mons[2].transform.parent.gameObject;
                m_box4 = Instantiate(src);
                m_box4.name = "ModMonster4";
                m_box4.transform.SetParent(src.transform.parent, false);
                m_box4.transform.localScale = src.transform.localScale;
                // its own clip plane and plain materials: the copy must not share (and overwrite) box 3's clip material
                BoxView.ResetCopiedClips(m_box4);
            }
            m_four = four;
            float step = (m_boxPos[2].x - m_boxPos[0].x) / 2f;   // 11
            for (int i = 0; i < 3; i++)
            {
                var p = m_boxPos[i];
                mons[i].transform.parent.localPosition = four ? new Vector3(m_boxPos[1].x + (i - 1.5f) * step, p.y, p.z) : p;
            }
            if (m_box4 != null)
            {
                m_box4.SetActive(four);
                m_box4.transform.localPosition = new Vector3(m_boxPos[1].x + 1.5f * step, m_boxPos[2].y, m_boxPos[2].z);
            }
        }

        void OnDestroy() { if (m_box4 != null) BoxView.DestroyClipMaterials(m_box4); }

        // ------------------------------------------------------------------ confirm
        void MsgModGodSilver() { Confirm(SlotTier.Silver); }
        void MsgModGodGold() { Confirm(SlotTier.Gold); }

        void Confirm(SlotTier t)
        {
            if (m_panel == null || Time.frameCount == m_frame) return;
            m_frame = Time.frameCount;
            var pd = SystemPlayers.GetPlayer(PlayerId);
            if (pd == null || pd.IsBot) return;
            if (!Unlocks.IsUnlocked(Unlocks.IdFor("God", t))) { SlotLock.Deny(m_panel); return; }
            var ed = SlotEditors.God != null ? SlotEditors.God(m_panel) : null;
            if (ed == null) { Chosen(t); return; }
            ed.Open(m_panel, PlayerId, t, () => Chosen(t), () => { m_dirty = true; });
        }

        /// <summary>The idol is chosen: the player's deity is theirs, then the origin page opens like after any god.</summary>
        void Chosen(SlotTier t)
        {
            Confirmed = t;
            var pd = SystemPlayers.GetPlayer(PlayerId);
            if (pd != null) pd.SetDeity(CustomGod.DeityFor(PlayerId, t));
            m_dirty = true;
            var picker = GetComponent<OriginPicker>() ?? gameObject.AddComponent<OriginPicker>();
            picker.Open(m_panel, false);
        }

        /// <summary>Vanilla OnSelect's tail for an idol (OnSelect itself would read the slot as a trial god).</summary>
        public static void FinishSelect(MenuDeitySelectPlayer panel)
        {
            var gs = Of(panel);
            var t = Selected(panel);
            int pid = R.Get<int>(panel, "m_playerId");
            var d = CustomGod.DeityFor(pid, t);
            var pd = SystemPlayers.GetPlayer(pid);
            if (pd != null && pd.GetDeity() != d) pd.SetDeity(d);
            if (gs != null) gs.m_dirty = true;
            panel.SendMessageUpwards("MsgQueueState", "DeitySelected");
            var portrait = R.Get<exSpriteAnimation>(panel, "m_portrait");
            if (portrait != null) portrait.SendMessage("MsgPlaySpawnEffect", SendMessageOptions.DontRequireReceiver);
            var perk = CustomGod.Get(pid, t).PerkGod;
            try { if (perk != null && perk.GetSoundSelected() != null) SystemAudio.Play(perk.GetSoundSelected()); } catch { }
        }
    }

    // =================================================================================================================
    //  The custom-god editor (two pages on the SlotEditorUI kit)
    // =================================================================================================================

    /// <summary>
    /// Page 1 picks the perk god (its portrait, name and perk text). Page 2 fills the 3 (silver) or 4 (gold) starter
    /// slots from a grid of every unlocked god's starters (the focused one runs in the big preview box; its name and
    /// god under the grid; a monster already in another slot is crossed out). DONE stores the picks.
    /// </summary>
    public class CustomGodEditor : ISlotEditor
    {
        // one per player id (panels come and go with scenes; an editor object holds no panel between opens)
        static readonly Dictionary<int, CustomGodEditor> s_by = new Dictionary<int, CustomGodEditor>();
        public static ISlotEditor For(MenuDeitySelectPlayer panel)
        {
            int pid = panel != null ? R.Get<int>(panel, "m_playerId") : -1;
            CustomGodEditor e;
            if (!s_by.TryGetValue(pid, out e)) s_by[pid] = e = new CustomGodEditor();
            return e;
        }

        SlotEditorUI m_ui;
        MenuDeitySelectPlayer m_panel;
        int m_pid;
        SlotTier m_tier;
        Action m_done, m_cancel;
        CustomGod.Record m_rec;
        List<Deity> m_gods;
        List<CustomGod.Starter> m_starters;
        int m_slot;
        GridRow m_grid;
        StripRow m_strip;
        int m_focusStarter;

        public bool IsOpen { get { return m_ui != null && m_ui.IsOpen; } }

        public void Open(MenuDeitySelectPlayer panel, int playerId, SlotTier tier, Action onDone, Action onCancel)
        {
            m_panel = panel; m_pid = playerId; m_tier = tier; m_done = onDone; m_cancel = onCancel;
            m_rec = CustomGod.Get(playerId, tier).Copy();
            m_gods = CustomGod.PerkGods();
            m_starters = CustomGod.StartersFor(tier, 0);
            m_ui = SlotEditorUI.For(panel);
            m_ui.Begin(panel, playerId, tier, CustomGod.TierName(tier));
            m_ui.onAbort = () => { if (m_cancel != null) m_cancel(); };   // nothing stored until DONE
            PagePerk();
        }

        public void Close() { if (m_ui != null) m_ui.End(); }

        int PerkIndex { get { for (int i = 0; i < m_gods.Count; i++) if (m_gods[i].GetName() == m_rec.perk) return i; return 0; } }

        void PagePerk()
        {
            m_ui.Clear();
            m_grid = null; m_strip = null;
            m_ui.onBack = () => { Close(); if (m_cancel != null) m_cancel(); };
            m_ui.SetPortraitFrom(() => m_gods.Count > 0 ? m_gods[PerkIndex].GetPortraitAnim() : null);
            m_ui.Add(new CycleRow
            {
                y = CycleRow.FirstY, label = "PERK OF",
                count = () => m_gods.Count,
                get = () => PerkIndex,
                set = i => { m_rec.perk = m_gods[i].GetName(); m_ui.SetPortraitFrom(() => m_gods[PerkIndex].GetPortraitAnim()); },
                name = i => m_gods[i].GetName().ToUpper(),
            });
            m_ui.Add(new InfoRow { y = CycleRow.FirstY - 9f, paragraph = true, wrap = 44f, line1 = () => m_gods.Count > 0 ? Sentence(CustomGod.PerkLine(m_gods[PerkIndex])) + " Only this perk applies." : "" });
            m_ui.Add(new ButtonRow { y = HeroEditor.ButtonY, text = "MONSTERS", onPress = PageStarters });
        }

        int IndexOf(string prefab)
        {
            for (int i = 0; i < m_starters.Count; i++) if (m_starters[i].p.gameObject.name == prefab) return i;
            return -1;
        }

        bool TakenElsewhere(int i)
        {
            string n = m_starters[i].p.gameObject.name;
            for (int k = 0; k < m_rec.starters.Count; k++) if (k != m_slot && m_rec.starters[k] == n) return true;
            return false;
        }

        /// <summary>Edit slot k: its own list (a gold idol's last slot ends with the secret), the grid cursor on the
        /// top-left monster.</summary>
        void SetSlot(int k)
        {
            m_slot = k;
            m_starters = CustomGod.StartersFor(m_tier, k);
            int at = k < m_rec.starters.Count ? IndexOf(m_rec.starters[k]) : -1;
            if (m_grid == null) { FocusStarter(at); return; }
            // every pick starts from the top left, not from where the last pick left the cursor
            m_grid.SetCursor(0);
            // on the strip the preview shows the slot's own monster; in the grid it follows the cursor
            FocusStarter(m_ui.Focused == m_grid || at < 0 ? 0 : at);
        }

        bool IsSecretAt(int i) { return i >= 0 && i < m_starters.Count && m_starters[i].god == null && CustomGod.IsSecret(m_starters[i].p.gameObject.name); }

        void PageStarters()
        {
            m_ui.Clear();
            m_slot = 0;
            m_starters = CustomGod.StartersFor(m_tier, 0);
            int slots = CustomGod.Slots(m_tier);
            m_strip = m_ui.Add(new StripRow
            {
                y = -63f, slots = slots, scale = 0.7f, pitch = 8.5f,
                at = k => k < m_rec.starters.Count ? CustomGod.StarterByName(m_rec.starters[k]) : null,
                current = () => m_slot,
                select = k => SetSlot(k),
                onPress = () => { if (m_grid != null) { SetSlot(m_slot); m_ui.FocusRow(m_grid); m_grid.Enter(1); } },
            });
            m_grid = m_ui.Add(new GridRow
            {
                y = -75f, cols = 4, visibleRows = 2, scale = 0.8f, pitchX = 9.5f, pitchY = 10.8f,
                cursor = 0,
                count = () => m_starters.Count,
                monsterAt = i => m_starters[i].p,
                taken = TakenElsewhere,
                special = IsSecretAt,
                onFocus = FocusStarter,
                onPick = i =>
                {
                    while (m_rec.starters.Count <= m_slot) m_rec.starters.Add("");
                    m_rec.starters[m_slot] = m_starters[i].p.gameObject.name;
                    if (m_slot < slots - 1) SetSlot(m_slot + 1);
                    else m_ui.Next();
                },
            });
            m_ui.Add(new InfoRow
            {
                y = -94.5f,
                line1 = () => m_focusStarter >= 0 && m_focusStarter < m_starters.Count ? SlotArt.MonsterName(m_starters[m_focusStarter].p.gameObject) : "",
                line2 = () => m_focusStarter < 0 || m_focusStarter >= m_starters.Count ? ""
                    : IsSecretAt(m_focusStarter) ? "the secret gold line"
                    : "of " + CustomGod.GodName(m_starters[m_focusStarter].god) + (TakenElsewhere(m_focusStarter) ? ", taken" : ""),
            });
            m_ui.Add(new ButtonRow { y = HeroEditor.ButtonY, text = "DONE", enabled = Valid, onPress = Done });
            m_ui.onBack = () =>
            {
                if (m_ui.Focused == m_grid) { m_ui.FocusRow(m_strip); SetSlot(m_slot); }
                else PagePerk();
            };
            m_ui.FocusRow(m_grid);
            FocusStarter(m_grid.cursor);
        }

        void FocusStarter(int i)
        {
            m_focusStarter = i;
            m_ui.SetPreviewMonster(i >= 0 && i < m_starters.Count ? m_starters[i].p : null);
            m_ui.RefreshAll();
        }

        static string Sentence(string s)
        {
            s = (s ?? "").Trim();
            return s.Length == 0 || s.EndsWith(".") || s.EndsWith("!") ? s : s + ".";
        }

        bool Valid() { return CustomGod.Valid(m_rec); }

        void Done()
        {
            CustomGod.Store(m_rec);
            Close();
            if (m_done != null) m_done();
        }
    }
}
