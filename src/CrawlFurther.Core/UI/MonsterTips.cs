using System;
using System.Collections.Generic;
using System.IO;
using BepInEx;
using BepInEx.Configuration;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.UI
{
    using CrawlFurther.Compat;
    using CrawlFurther.Ghosts;
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Monster tips: whenever a human player takes control of a monster body (spawning or possessing at the start of a
    /// room, rising from a statue, inhabiting fodder, the first body after an evolution, a boss part), a short note
    /// above that player's own HUD panel says what that monster's attack, special and passive do (<see cref="TipView"/>:
    /// every player's tip at once, each in its own column). Shown 7 s (+1 s per passive line; 5 s and two lines with 3-4
    /// players), then fades over 1 s. The same text is the first page of Pause > Tips. The text comes from
    /// <see cref="TipRegistry"/>. Settings: BepInEx/config/CrawlMod.Tips.cfg [General] TipsFor (All, P1, Off) and
    /// Tooltips (Always, FirstTime, Off), both also in the game's Options menu ("Tips: ALL / P1 ONLY / OFF" and
    /// "Tooltips: ALWAYS / FIRST TIME / OFF"). FirstTime reads BepInEx/config/CrawlMod.TipsSeen.txt, the monsters each
    /// save (profile) has taken.
    /// </summary>
    public static class MonsterTips
    {
        public const float ShowTime = 7f, FadeTime = 1f, FadeInTime = 0.15f;
        /// <summary>Extra reading time per body line beyond the attack and special lines (a 2-line passive: +2 s).</summary>
        public const float ShowPerLine = 1f;
        const int MaxPlayers = 8;

        /// <summary>Who sees tips: every human player, only player 1, or nobody.</summary>
        public enum Mode { All, P1, Off }

        /// <summary>When a player sees a monster's tip: every time they take it, only the first time their save takes
        /// it, or never.</summary>
        public enum Repeat { Always, FirstTime, Off }

        static ConfigFile s_cfg;
        static ConfigEntry<bool> s_show;
        static ConfigEntry<Mode> s_mode;
        static ConfigEntry<Repeat> s_repeat;
        static bool s_cfgTried;
        static Mode s_fallback = Mode.All;
        static Repeat s_repeatFallback = Repeat.Always;

        /// <summary>One take can call both body hooks (InitAsPlayer, OnInhabitAI): the same key again this soon is the same take.</summary>
        const float SameTake = 2f;
        // per player: the last tip key shown and when (the double-hook guard above)
        static readonly string[] s_recentKey = new string[MaxPlayers];
        static readonly float[] s_recentAt = new float[MaxPlayers];

        // the monsters each save has taken, "profile\tkey" (CrawlMod.TipsSeen.txt)
        const string SeenFile = "CrawlMod.TipsSeen.txt";
        static readonly HashSet<string> s_taken = new HashSet<string>();
        static bool s_takenLoaded, s_takenUnreadable;
        static readonly HashSet<string> s_missingLogged = new HashSet<string>();
        static bool s_audited;
        // per player: the last body / boss part they took (kept even with tips off: the pause menu's page reads it)
        static readonly string[] s_lastKey = new string[MaxPlayers];
        static readonly int[] s_lastRoom = new int[MaxPlayers];

        static void InitConfig()
        {
            if (s_cfgTried) return;
            s_cfgTried = true;
            try
            {
                s_cfg = new ConfigFile(Path.Combine(Paths.ConfigPath, "CrawlMod.Tips.cfg"), true);
                s_show = s_cfg.Bind("General", "ShowMonsterTips", true,
                    "Old switch: false turns tips off. TipsFor below is the setting now.");
                s_mode = s_cfg.Bind("General", "TipsFor", s_show.Value ? Mode.All : Mode.Off,
                    "Who sees the short tips (a monster's attack and special when a player becomes it, an object's use " +
                    "near it): All = every player, each above their own HUD panel; P1 = only player 1; Off = none. Also set " +
                    "in the game's Options menu (Tips: ALL / P1 ONLY / OFF).");
                s_repeat = s_cfg.Bind("General", "Tooltips", Repeat.Always,
                    "When a monster's tip shows: Always = every time a player takes that monster; FirstTime = only the " +
                    "first time that player's save (profile) takes it (kept in CrawlMod.TipsSeen.txt); Off = never. Off " +
                    "here or in TipsFor hides tips. Also set in the game's Options menu (Tooltips: ALWAYS / FIRST TIME / OFF).");
            }
            catch (Exception e) { FurtherCore.Log.LogError("Monster tips: config failed, using defaults: " + e.Message); }
        }

        public static Mode TipsFor
        {
            get { InitConfig(); return s_mode != null ? s_mode.Value : s_fallback; }
            set
            {
                InitConfig();
                if (s_mode != null) s_mode.Value = value;   // SaveOnConfigSet: written to the .cfg straight away
                else s_fallback = value;
                if (s_show != null) s_show.Value = value != Mode.Off;
                if (value == Mode.Off) TipView.HideAll();
                FurtherCore.Log.LogInfo("Tips: " + value);
            }
        }

        /// <summary>When monster tips show: every take, a save's first take of each monster, or never.</summary>
        public static Repeat Tooltips
        {
            get { InitConfig(); return s_repeat != null ? s_repeat.Value : s_repeatFallback; }
            set
            {
                InitConfig();
                if (s_repeat != null) s_repeat.Value = value;   // SaveOnConfigSet: written to the .cfg straight away
                else s_repeatFallback = value;
                if (value == Repeat.Off) TipView.HideAll();
                FurtherCore.Log.LogInfo("Tooltips: " + value);
            }
        }

        /// <summary>Tips are on for someone (the object and monster hooks check this before any work). Off in either
        /// setting is off.</summary>
        public static bool Enabled
        {
            get { return TipsFor != Mode.Off && Tooltips != Repeat.Off; }
            set
            {
                TipsFor = value ? Mode.All : Mode.Off;
                if (value && Tooltips == Repeat.Off) Tooltips = Repeat.Always;
            }
        }

        /// <summary>Does this player get tips? All: every player id; P1: only player 1. Never with Tooltips off.</summary>
        public static bool ShowFor(int playerId)
        {
            if (Tooltips == Repeat.Off) return false;
            var m = TipsFor;
            return m == Mode.All || (m == Mode.P1 && playerId == 0);
        }

        /// <summary>The save a player plays on: their profile's name (or their slot when they have none).</summary>
        static string SaveOf(PlayerData pd)
        {
            string name = null;
            try { if (pd.Profile != null) name = pd.Profile.m_name; } catch { }
            if (string.IsNullOrEmpty(name)) return "(no profile) P" + (pd.Id + 1);
            return name.Replace('\t', ' ').Replace('\r', ' ').Replace('\n', ' ');
        }

        static void LoadTaken()
        {
            if (s_takenLoaded) return;
            s_takenLoaded = true;
            try
            {
                var path = Path.Combine(Paths.ConfigPath, SeenFile);
                if (!File.Exists(path)) return;
                foreach (var raw in File.ReadAllLines(path))
                    if (raw.IndexOf('\t') > 0) s_taken.Add(raw);   // the header line has no tab
            }
            catch (Exception e)
            {
                // never write over a list we could not read: this session's takes stay in memory only
                s_takenUnreadable = true;
                FurtherCore.Log.LogWarning("Monster tips: could not read " + SeenFile + " (it is left as it is): " + e.Message);
            }
        }

        static void SaveTaken()
        {
            if (s_takenUnreadable) return;
            try
            {
                var lines = new List<string> { "# Monsters each save has taken (profile, tab, monster). Tooltips = FirstTime shows a tip only for monsters not listed. Delete a line to see that tip again." };
                var all = new List<string>(s_taken); all.Sort(StringComparer.Ordinal);
                lines.AddRange(all);
                File.WriteAllLines(Path.Combine(Paths.ConfigPath, SeenFile), lines.ToArray());
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Monster tips: could not write " + SeenFile + ": " + e.Message); }
        }

        /// <summary>Record that this player's save took the monster; true the first time it has.</summary>
        static bool MarkTaken(PlayerData pd, string key)
        {
            LoadTaken();
            if (!s_taken.Add(SaveOf(pd) + "\t" + key)) return false;
            SaveTaken();
            return true;
        }

        internal static int RoomId()
        {
            try
            {
                if (!Singleton<SystemLevel>.HasInstance()) return 0;
                var r = SystemLevel.GetCurrentRoom();
                return r != null ? r.GetInstanceID() : 0;
            }
            catch { return 0; }
        }

        static bool IsHumanMonster(PlayerData pd)
        {
            return pd != null && pd.IsHuman && !pd.IsBot && !pd.IsBossOnlyBot && !pd.IsHero && pd.Id >= 0 && pd.Id < MaxPlayers;
        }

        /// <summary>
        /// The tip key of a ghost body, or null for none (plain ghosts are not monsters). Set it when a ghost form of your
        /// mod has an attack worth a tip. InitAsPlayer renames every ghost "Ghost", so tell forms apart by their
        /// components or attack list, not their name.
        /// </summary>
        public static Func<Player, string> GhostKey;

        /// <summary>The tip key for a body: its prefab name, <see cref="GhostKey"/> for ghosts, null for heroes.</summary>
        static string KeyOf(Player body)
        {
            if (body == null || R.Get<bool>(body, "m_isHero")) return null;
            if (R.Get<bool>(body, "m_isGhost")) return GhostKey != null ? GhostKey(body) : null;
            return ModUtil.PrefabName(body.gameObject);
        }

        static void Remember(PlayerData pd, string key)
        {
            if (pd == null || pd.Id < 0 || pd.Id >= MaxPlayers) return;
            s_lastKey[pd.Id] = key;
            s_lastRoom[pd.Id] = RoomId();
        }

        /// <summary>
        /// The tip key of what <paramref name="pd"/> controls right now (the pause menu's "you" page): the monster body,
        /// a ghost with a <see cref="GhostKey"/>, or the boss part they last took in this room while they are a ghost in a trap.
        /// Null for the hero, plain ghosts and players with no body.
        /// </summary>
        public static string CurrentKey(PlayerData pd)
        {
            if (pd == null || pd.IsHero) return null;
            var go = pd.GameObject;
            var body = go != null ? go.GetComponent<Player>() : null;
            if (body == null) return null;
            if (R.Get<bool>(body, "m_isHero")) return null;
            if (R.Get<bool>(body, "m_isGhost"))
            {
                int id = pd.Id;
                if (id >= 0 && id < MaxPlayers && s_lastKey[id] != null && s_lastRoom[id] == RoomId() && s_lastKey[id].IndexOf('/') > 0)
                    return s_lastKey[id];   // a ghost inside a boss part
            }
            var key = KeyOf(body);
            return Unwritten(key) ? null : key;
        }

        /// <summary>
        /// In a fight against another mod's boss, a body or part with no written tip gets none: the generic tip would
        /// guess at content we know nothing about and cover that mod's own boss UI.
        /// </summary>
        static bool Unwritten(string key)
        {
            MonsterTip t;
            return key != null && !TipRegistry.TryGet(key, out t) && CompatBosses.ForeignFight;
        }

        /// <summary>The tip for a key: the table's, else the generic one the HUD tip would show.</summary>
        public static MonsterTip TipFor(string key, Player body)
        {
            MonsterTip tip;
            return TipRegistry.TryGet(key, out tip) ? tip : Fallback(key, body);
        }

        /// <summary>A Player body was just given to <paramref name="pd"/> (InitAsPlayer / OnInhabitAI).</summary>
        public static void OnBody(Player body, PlayerData pd)
        {
            if (body == null || !IsHumanMonster(pd)) return;
            string key = KeyOf(body);
            if (key == null || Unwritten(key)) return;
            Remember(pd, key);
            bool first = MarkTaken(pd, key);
            if (!Enabled) return;
            Show(pd, key, body, first);
        }

        /// <summary>A player entered a trap. Only boss parts get a tip (room traps are props, not monsters).</summary>
        public static void OnTrap(PropTrap trap, Player actioner)
        {
            if (trap == null || actioner == null) return;
            var pd = actioner.GetPlayerData();
            if (!IsHumanMonster(pd)) return;
            string part = ModUtil.PrefabName(trap.gameObject);
            var boss = trap.GetComponentInParent<Boss>();
            string key;
            if (boss != null)
            {
                key = ModUtil.PrefabName(boss.gameObject) + "/" + part;
                MonsterTip t;
                if (!TipRegistry.TryGet(key, out t) && TipRegistry.TryGet(part, out t)) key = part;
            }
            else if (part.StartsWith("Boss", StringComparison.Ordinal)) key = part;   // parts spawned on their own (summoned arms)
            else return;
            if (Unwritten(key)) return;
            Remember(pd, key);
            bool first = MarkTaken(pd, key);
            if (!Enabled) return;
            Show(pd, key, null, first);
        }

        /// <summary>first: this is the first time the player's save has taken the monster.</summary>
        static void Show(PlayerData pd, string key, Player body, bool first)
        {
            int id = pd.Id;
            var repeat = Tooltips;
            if (repeat == Repeat.Off || (repeat == Repeat.FirstTime && !first)) return;
            float now = Time.unscaledTime;
            if (s_recentKey[id] == key && now - s_recentAt[id] < SameTake) return;   // the other hook of the same take
            s_recentKey[id] = key;
            s_recentAt[id] = now;
            Audit();

            MonsterTip tip;
            if (!TipRegistry.TryGet(key, out tip)) tip = Fallback(key, body);
            string name = tip.name;
            string who = null;
            try { if (SystemPlayers.GetNumHumanPlayers() > 1) who = "P" + (id + 1); } catch { }
            Color colour = Color.white;
            try { if (pd.Setup != null) colour = pd.Setup.m_colourGUI; } catch { }
            colour.a = 1f;
            // a passive may run to a second line ("\n"): the renderer counts the lines
            string passive = string.IsNullOrEmpty(tip.passive) ? null : "Passive: " + tip.passive;
            // a line that names the ghost button names this player's own button
            string button = GhostControls.Name(pd);
            TipView.Get().Show(id, who != null ? who + " - " + name : name, GhostControls.Personalise("Attack: " + tip.attack, button),
                               GhostControls.Personalise("Special: " + tip.special, button), GhostControls.Personalise(passive, button), colour, true);
        }

        static MonsterTip Fallback(string key, Player body)
        {
            if (s_missingLogged.Add(key)) FurtherCore.Log.LogWarning("Monster tips: no tip written for '" + key + "', showing a generic one");
            bool special = false;
            try { special = body != null && R.Get<bool>(body, "m_hasSpecialAttack"); } catch { }
            string pretty = key;
            int slash = pretty.LastIndexOf('/');
            if (slash >= 0) pretty = pretty.Substring(slash + 1);
            if (pretty.StartsWith("Enemy", StringComparison.Ordinal)) pretty = pretty.Substring(5);
            else if (pretty.StartsWith("Mod", StringComparison.Ordinal)) pretty = pretty.Substring(3);
            var sb = new System.Text.StringBuilder();
            for (int i = 0; i < pretty.Length; i++)
            {
                char c = pretty[i];
                if (c == '_') { sb.Append(' '); continue; }
                if (i > 0 && char.IsUpper(c) && !char.IsUpper(pretty[i - 1]) && pretty[i - 1] != '_') sb.Append(' ');
                sb.Append(c);
            }
            return new MonsterTip(sb.ToString().Trim(), "Its basic attack - try it out",
                body == null ? "none, aim with movement" : special ? "Fills up over time - use it when ready" : "none");
        }

        /// <summary>Once per session: say in the log which built mod monsters have no tip text.</summary>
        static void Audit()
        {
            if (s_audited) return;
            s_audited = true;
            try
            {
                var missing = new List<string>();
                int mod = 0;
                foreach (var id in MonsterFactory.Built.Keys)
                {
                    mod++;
                    MonsterTip t;
                    if (!TipRegistry.TryGet("Mod" + id, out t)) missing.Add("Mod" + id);
                }
                FurtherCore.Log.LogInfo("Monster tips: " + TipRegistry.Tips.Count + " entries (+" + TipRegistry.Alias.Count +
                                   " aliases); " + mod + " mod monsters built" + (missing.Count > 0 ? ", missing: " + string.Join(", ", missing.ToArray()) : ", all covered"));
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Monster tips audit failed: " + e.Message); }
        }
    }

    // ------------------------------------------------------------------ hooks

    /// <summary>Spawning as a monster (room start, statues, spawners, after a ghost spell, evolutions), the tutorial and challenge monsters.</summary>
    [HarmonyPatch(typeof(Player), "InitAsPlayer")]
    static class Patch_TipsInitAsPlayer
    {
        static void Postfix(Player __instance, PlayerData playerData)
        {
            try { MonsterTips.OnBody(__instance, playerData); }
            catch (Exception e) { FurtherCore.Log.LogError("Monster tips (InitAsPlayer) failed: " + e.Message); }
        }
    }

    /// <summary>A ghost inhabiting fodder or an AI monster (PropFodder sends OnInhabitAI).</summary>
    [HarmonyPatch(typeof(Player), "OnInhabitAI")]
    static class Patch_TipsInhabit
    {
        static void Postfix(Player __instance, PlayerData playerData)
        {
            try { MonsterTips.OnBody(__instance, playerData); }
            catch (Exception e) { FurtherCore.Log.LogError("Monster tips (OnInhabitAI) failed: " + e.Message); }
        }
    }

    /// <summary>A ghost taking a boss part (every boss part is a PropTrap; the subclasses call this base method).</summary>
    [HarmonyPatch(typeof(PropTrap), "OnAction")]
    static class Patch_TipsTrap
    {
        static void Postfix(PropTrap __instance, Player actioner, bool __result)
        {
            if (!__result) return;
            try { MonsterTips.OnTrap(__instance, actioner); }
            catch (Exception e) { FurtherCore.Log.LogError("Monster tips (trap) failed: " + e.Message); }
        }
    }

    /// <summary>Options menu: adds "Tips: ALL / P1 ONLY / OFF" and "Tooltips: ALWAYS / FIRST TIME / OFF" at the end of the options list.</summary>
    [HarmonyPatch(typeof(MenuOptions), "InitMenuText")]
    static class Patch_TipsOptions
    {
        static void Postfix(MenuOptions __instance)
        {
            try { MonsterTipsOption.Attach(__instance); }
            catch (Exception e) { FurtherCore.Log.LogError("Monster tips option failed: " + e.Message); }
        }
    }
}
