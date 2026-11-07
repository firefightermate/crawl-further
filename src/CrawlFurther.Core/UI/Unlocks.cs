using System;
using System.Collections.Generic;

namespace CrawlFurther.UI
{
    using CrawlFurther.Compat;
    using CrawlFurther.Gods;

    /// <summary>
    /// Unlock challenges (see <see cref="UnlockDef"/>) and the counters they read. Counters persist across games in
    /// BepInEx/config/CrawlFurther.Unlocks.cfg; Core's own hooks (UnlockHooks) count the Stat... counters for human
    /// players. A challenge that completes is announced with a banner on the next menu. The debug setting UnlockAll
    /// (BepInEx/config/CrawlMod.Debug.cfg) opens every challenge without touching the counters.
    /// </summary>
    public static class Unlocks
    {
        /// <summary>Counters Core counts: monsters and fodder the hero kills, games won as the hero, evolutions, distinct
        /// final forms reached, ectoplasm a ghost banks, heroes slain as a monster.</summary>
        public const string StatHeroKills = "HeroKills", StatWins = "HeroWins", StatEvolutions = "Evolutions",
                            StatFinals = "FinalForms", StatEcto = "Ectoplasm", StatHeroSlain = "HeroesSlain";

        public static readonly List<UnlockDef> All = new List<UnlockDef>();

        /// <summary>True while ectoplasm a ghost receives is a refund rather than gathered: it does not count toward
        /// <see cref="StatEcto"/> (a refund would farm the count).</summary>
        public static Func<bool> EctoRefunding;

        /// <summary>Add a challenge, or replace the one with the same id.</summary>
        public static void Add(UnlockDef def)
        {
            if (def == null || string.IsNullOrEmpty(def.id)) return;
            for (int i = 0; i < All.Count; i++) if (All[i].id == def.id) { All[i] = def; return; }
            All.Add(def);
        }

        static readonly Dictionary<string, int> s_counts = new Dictionary<string, int>();
        static readonly Dictionary<string, HashSet<string>> s_sets = new Dictionary<string, HashSet<string>>();
        static readonly Dictionary<string, float> s_fraction = new Dictionary<string, float>();
        /// <summary>Completed this session and not yet announced (UnlockToast shows them on the next menu).</summary>
        public static readonly Queue<UnlockDef> Announce = new Queue<UnlockDef>();
        static bool s_loaded, s_dirty;
        static float s_lastSave;
        static bool? s_unlockAll;

        public const string FILE = "CrawlFurther.Unlocks.cfg";
        static string Path { get { return System.IO.Path.Combine(BepInEx.Paths.ConfigPath, FILE); } }

        /// <summary>CrawlMod.Debug.cfg [Unlocks] UnlockAll: every challenge counts as done, for testing.</summary>
        public static bool UnlockAll
        {
            get
            {
                if (s_unlockAll == null)
                {
                    try
                    {
                        var cfg = new BepInEx.Configuration.ConfigFile(System.IO.Path.Combine(BepInEx.Paths.ConfigPath, "CrawlMod.Debug.cfg"), true);
                        s_unlockAll = cfg.Bind("Unlocks", "UnlockAll", false,
                            "Open everything the unlock challenges lock (the silver and gold slots) without doing them. For testing; progress is kept.").Value;
                    }
                    catch { s_unlockAll = false; }
                }
                return s_unlockAll.Value;
            }
        }

        /// <summary>Test mode's "unlock everything for this session" is on: every challenge and secret reads as done,
        /// nothing is counted or saved.</summary>
        internal static bool OpenForTest { get { return Testing.TestCheats.UnlockAll && Testing.TestMode.Active; } }

        /// <summary>Has the challenge been completed (or forced on by the debug config)?</summary>
        public static bool IsUnlocked(string id)
        {
            var c = Find(id);
            if (c == null) return false;
            if (UnlockAll || OpenForTest) return true;
            // hosting online with Crawl Online's UnlockEverything on: open for the session (nothing saved)
            if (CompatOnline.SessionUnlockAll) return true;
            return Get(c.stat) >= c.target;
        }

        /// <summary>"Kill 400 monsters as the hero  (123 / 400)".</summary>
        public static string ProgressText(string id)
        {
            var c = Find(id);
            if (c == null) return "";
            return c.text + "  (" + Math.Min(Get(c.stat), c.target) + " / " + c.target + ")";
        }

        /// <summary>Short progress for tight panels: "123 / 400".</summary>
        public static string ProgressShort(string id)
        {
            var c = Find(id);
            return c == null ? "" : Math.Min(Get(c.stat), c.target) + " / " + c.target;
        }

        /// <summary>The id of the challenge that opens the <paramref name="tier"/> slot of a picker list: the list name plus
        /// "Silver" or "Gold" ("Hero" -> "HeroSilver"); null for a normal slot.</summary>
        public static string IdFor(string list, SlotTier tier)
        {
            if (tier == SlotTier.Normal) return null;
            return list + (tier == SlotTier.Silver ? "Silver" : "Gold");
        }

        /// <summary>Add to a persistent counter. Persists (batched) and queues an announcement when it completes a challenge.</summary>
        public static void Count(string stat, int n = 1)
        {
            if (string.IsNullOrEmpty(stat) || n == 0) return;
            Load();
            UnlockToast.Ensure();
            int before = Get(stat);
            s_counts[stat] = before + n;
            s_dirty = true;
            foreach (var c in All)
                if (c.stat == stat && before < c.target && before + n >= c.target)
                {
                    Announce.Enqueue(c);
                    FurtherCore.Log.LogInfo("Unlocked: " + c.slot + " (" + c.text + ")");
                    Save();
                }
        }

        /// <summary>A fractional counter (a pickup worth half a unit, say): whole units go to Count.</summary>
        public static void CountFraction(string stat, float amount)
        {
            if (amount <= 0f) return;
            float f;
            s_fraction.TryGetValue(stat, out f);
            f += amount;
            int whole = (int)Math.Floor(f + 1e-4f);
            s_fraction[stat] = f - whole;
            if (whole > 0) Count(stat, whole);
        }

        /// <summary>Count <paramref name="key"/> once ever for <paramref name="stat"/> (e.g. distinct final forms).</summary>
        public static bool CountDistinct(string stat, string key)
        {
            if (string.IsNullOrEmpty(key)) return false;
            Load();
            HashSet<string> set;
            if (!s_sets.TryGetValue(stat, out set)) s_sets[stat] = set = new HashSet<string>();
            if (!set.Add(key)) return false;
            Count(stat, 1);
            return true;
        }

        public static int Get(string stat) { Load(); int v; return s_counts.TryGetValue(stat, out v) ? v : 0; }

        public static UnlockDef Find(string id)
        {
            foreach (var c in All) if (c.id == id) return c;
            return null;
        }

        // ------------------------------------------------------------------ persistence (plain "key = value" lines)
        public static void Load()
        {
            if (s_loaded) return;
            s_loaded = true;
            try
            {
                if (!System.IO.File.Exists(Path)) return;
                foreach (var raw in System.IO.File.ReadAllLines(Path))
                {
                    var line = raw.Trim();
                    if (line.Length == 0 || line[0] == '#' || line[0] == '[') continue;
                    int eq = line.IndexOf('=');
                    if (eq <= 0) continue;
                    string k = line.Substring(0, eq).Trim(), v = line.Substring(eq + 1).Trim();
                    if (k.StartsWith("Seen.", StringComparison.Ordinal))
                    {
                        var set = new HashSet<string>();
                        foreach (var e in v.Split(',')) if (e.Trim().Length > 0) set.Add(e.Trim());
                        s_sets[k.Substring(5)] = set;
                    }
                    else
                    {
                        int n;
                        if (int.TryParse(v, out n)) s_counts[k] = Math.Max(0, n);
                    }
                }
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Unlocks: could not read " + FILE + ": " + e.Message); }
        }

        /// <summary>Write the counters now if anything changed.</summary>
        public static void Save()
        {
            if (!s_dirty) return;
            try
            {
                var sb = new System.Text.StringBuilder();
                sb.AppendLine("# Progress toward the unlock challenges. Written by the mod.");
                sb.AppendLine("# Editing a number changes your progress; delete the file to start over.");
                foreach (var c in All)
                    sb.AppendLine("# " + c.slot + ": " + c.text + " (" + c.stat + " >= " + c.target + ")");
                sb.AppendLine("[Counters]");
                var keys = new List<string>(s_counts.Keys); keys.Sort(StringComparer.Ordinal);
                foreach (var k in keys) sb.AppendLine(k + " = " + s_counts[k]);
                var sk = new List<string>(s_sets.Keys); sk.Sort(StringComparer.Ordinal);
                foreach (var k in sk)
                {
                    var l = new List<string>(s_sets[k]); l.Sort(StringComparer.Ordinal);
                    sb.AppendLine("Seen." + k + " = " + string.Join(",", l.ToArray()));
                }
                System.IO.File.WriteAllText(Path, sb.ToString());
                s_dirty = false;
                s_lastSave = UnityEngine.Time.realtimeSinceStartup;
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Unlocks: could not write " + FILE + ": " + e.Message); }
        }

        /// <summary>Called every frame by UnlockToast: kills and pickups batch up, written at most every 5 s.</summary>
        public static void Tick()
        {
            if (s_dirty && UnityEngine.Time.realtimeSinceStartup - s_lastSave > 5f) Save();
        }

        /// <summary>Self-test: every challenge is well formed and plain.</summary>
        public static void SelfCheck(Action<string> bad)
        {
            var ids = new HashSet<string>();
            foreach (var c in All)
            {
                if (!ids.Add(c.id)) bad("Unlocks: duplicate challenge " + c.id);
                if (c.target <= 0) bad("Unlocks: " + c.id + " target " + c.target);
                if (string.IsNullOrEmpty(c.stat)) bad("Unlocks: " + c.id + " has no counter");
                if (string.IsNullOrEmpty(c.text) || c.text.Length > 40) bad("Unlocks: " + c.id + " text length " + (c.text ?? "").Length);
                foreach (char ch in c.text + c.title + c.slot) if ("%{|}~[]#".IndexOf(ch) >= 0) bad("Unlocks: " + c.id + " uses '" + ch + "'");
            }
        }
    }
}
