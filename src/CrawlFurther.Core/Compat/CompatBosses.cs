using System;
using System.Collections;
using System.Collections.Generic;
using System.Reflection;
using HarmonyLib;

namespace CrawlFurther.Compat
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Other mods that add final bosses, with CrawlCustomBosses (PandasProjects: CrawlBossKit plus six boss plugins,
    /// GUIDs com.zac.*) as the case we test against. Reflection only: no compile-time reference, and the rules below are
    /// generic, so they hold for any boss mod that clones a vanilla boss room.
    /// <list type="bullet">
    /// <item>The final boss pick: <see cref="BossFactory"/> runs last on SystemGame.CalcNextBoss and replaces only a
    /// vanilla pick (<see cref="IsVanillaBoss"/>), so a boss another mod chose for the run is never swapped out, and a
    /// kit that resets "vanilla" runs to the recorded vanilla boss no longer erases ours.</item>
    /// <item>Boss arenas (<see cref="IsBossArena"/>): room objects never spawn in one.</item>
    /// <item>A fight against a boss of another mod (<see cref="ForeignFight"/>): monster tips only show text that was
    /// written for what the player controls; there is no generic tip for parts we know nothing about.</item>
    /// </list>
    /// </summary>
    public static class CompatBosses
    {
        /// <summary>CrawlBossKit's plugin GUID (also its Harmony id).</summary>
        public const string KitGuid = "com.zac.crawlbosskit";
        /// <summary>LabyrinthBoss's plugin GUID (also its Harmony id); it rolls its own boss when the kit is absent.</summary>
        public const string LabyrinthGuid = "com.zac.labyrinthboss";

        static readonly string[] s_knownGuids =
        {
            KitGuid, LabyrinthGuid, "com.zac.boss.cthulhu", "com.zac.boss.dragon", "com.zac.boss.goblinking",
            "com.zac.boss.kraken", "com.zac.boss.wizard",
        };

        static readonly AccessTools.FieldRef<BossEncounter, Boss> s_encounterBoss =
            AccessTools.FieldRefAccess<BossEncounter, Boss>("m_prefabBoss");
        static readonly AccessTools.FieldRef<BossEncounter, Room> s_encounterRoom =
            AccessTools.FieldRefAccess<BossEncounter, Room>("m_bossRoom");
        static readonly MethodInfo m_calcNextBoss = AccessTools.Method(typeof(SystemGame), "CalcNextBoss");

        /// <summary>A known boss mod (any CrawlCustomBosses plugin) is loaded.</summary>
        public static bool Present
        {
            get
            {
                foreach (var g in s_knownGuids) if (Loaded(g) != null) return true;
                return false;
            }
        }

        static BepInEx.PluginInfo Loaded(string guid)
        {
            BepInEx.PluginInfo info;
            return BepInEx.Bootstrap.Chainloader.PluginInfos.TryGetValue(guid, out info) && info != null && info.Instance != null ? info : null;
        }

        /// <summary>True for one of the game's own bosses (the prefabs vanilla picks from).</summary>
        public static bool IsVanillaBoss(Boss boss)
        {
            if (boss == null) return false;
            try
            {
                var all = Singleton<Constants>.Get.m_bosses;
                if (all != null) foreach (var b in all) if (b == boss) return true;
            }
            catch { }
            return false;
        }

        /// <summary>True for a boss prefab that is neither vanilla nor one of ours (<see cref="BossFactory.Built"/>).</summary>
        public static bool IsForeignBoss(Boss boss)
        {
            return boss != null && !IsVanillaBoss(boss) && !BossFactory.Built.Contains(boss);
        }

        /// <summary>The boss prefab of the running (or last) boss encounter, or null.</summary>
        public static Boss EncounterBoss
        {
            get
            {
                try
                {
                    var enc = SystemLevel.GetBossEncounter();
                    return enc != null ? s_encounterBoss(enc) : null;
                }
                catch { return null; }
            }
        }

        /// <summary>A boss encounter is running and its boss comes from another mod.</summary>
        public static bool ForeignFight
        {
            get
            {
                try { return SystemLevel.GetBossEncounterActive() && IsForeignBoss(EncounterBoss); }
                catch { return false; }
            }
        }

        /// <summary>
        /// A boss room: flagged by its prefab (every vanilla boss room, and every arena cloned from one, which is how boss
        /// mods build theirs) or the room the running encounter spawned.
        /// </summary>
        public static bool IsBossArena(Room room)
        {
            if (room == null) return false;
            if (room.m_bossRoom) return true;
            try
            {
                var enc = SystemLevel.GetBossEncounter();
                return enc != null && s_encounterRoom(enc) == room;
            }
            catch { return false; }
        }

        // ---------------------------------------------------------------- self-test
        /// <summary>Self-test section: the boss mods found, their bosses, and every method both sides patch.</summary>
        public static void SelfCheck(Action<string> bad, Action<string> note)
        {
            var owners = ForeignBossOwners();
            var shown = new HashSet<string>();
            foreach (var g in s_knownGuids)
            {
                var info = Loaded(g);
                if (info == null) continue;
                shown.Add(g);
                note(info.Metadata.Name + " " + info.Metadata.Version + " (" + g + ")");
            }
            foreach (var o in owners)
                if (shown.Add(o)) note("another mod picks final bosses: Harmony id " + o);
            if (shown.Count == 0) { note("no other boss mod installed: nothing to check"); return; }

            ListKitBosses(bad, note);
            CheckBossPickOrder(bad, note);
            SharedPatches(bad, note, shown);
            note("  check by hand in game: docs/compat.md, Boss mods");
        }

        /// <summary>Harmony ids, other than ours, that patch SystemGame.CalcNextBoss: whoever they are, they pick bosses.</summary>
        static List<string> ForeignBossOwners()
        {
            var list = new List<string>();
            var info = m_calcNextBoss != null ? Harmony.GetPatchInfo(m_calcNextBoss) : null;
            if (info == null) return list;
            foreach (var o in info.Owners) if (!FurtherCore.IsOurHarmonyId(o) && !list.Contains(o)) list.Add(o);
            return list;
        }

        /// <summary>CrawlBossKit's registered bosses (BossKit.Kit.Bosses): name, built or not, rotation settings.</summary>
        static void ListKitBosses(Action<string> bad, Action<string> note)
        {
            var kit = Loaded(KitGuid);
            if (kit == null) return;
            try
            {
                var t = kit.Instance.GetType().Assembly.GetType("BossKit.Kit", false);
                var p = t != null ? t.GetProperty("Bosses", BindingFlags.Public | BindingFlags.Static) : null;
                var bosses = p != null ? p.GetValue(null, null) as IEnumerable : null;
                if (bosses == null) { note("  CrawlBossKit's boss list (BossKit.Kit.Bosses) not found: bosses not listed"); return; }
                int n = 0;
                foreach (var ctx in bosses)
                {
                    n++;
                    var info = Prop(ctx, "Info");
                    string name = info != null ? Field(info, "TemplateName") as string : null;
                    object ready = Prop(ctx, "Ready"), failure = Prop(ctx, "Failure");
                    note("  kit boss " + (name ?? "?") + ": " + (true.Equals(ready) ? "built" : "not built" + (failure != null ? " (" + failure + ")" : ""))
                         + ", mode " + Entry(Prop(ctx, "Mode")) + ", weight " + Entry(Prop(ctx, "Weight")) + ", enabled " + Entry(Prop(ctx, "Enabled")));
                    var template = Prop(ctx, "Template") as Boss;
                    if (template != null && !IsForeignBoss(template)) bad("kit boss " + name + " is not recognised as another mod's boss");
                }
                note("  " + n + " kit boss(es) registered");
            }
            catch (Exception e) { note("  CrawlBossKit's bosses could not be read: " + e.Message); }
        }

        /// <summary>Our CalcNextBoss postfix must run after every other mod's, so it sees their final pick.</summary>
        static void CheckBossPickOrder(Action<string> bad, Action<string> note)
        {
            var info = m_calcNextBoss != null ? Harmony.GetPatchInfo(m_calcNextBoss) : null;
            if (info == null) { note("  SystemGame.CalcNextBoss is not patched"); return; }
            var sorted = PatchProcessor.GetSortedPatchMethods(m_calcNextBoss, new List<Patch>(info.Postfixes).ToArray());
            var line = new List<string>();
            int ours = -1, lastForeign = -1;
            for (int i = 0; i < sorted.Count; i++)
            {
                string owner = null;
                foreach (var pf in info.Postfixes) if (pf.PatchMethod == sorted[i]) owner = pf.owner;
                bool mine = owner != null && FurtherCore.IsOurHarmonyId(owner);
                if (mine) ours = i; else lastForeign = i;
                line.Add(sorted[i].DeclaringType.Name + "." + sorted[i].Name + (mine ? " (ours)" : ""));
            }
            note("  CalcNextBoss postfixes in order: " + string.Join(", ", line.ToArray()));
            if (ours >= 0 && ours < lastForeign) bad("our CalcNextBoss postfix runs before another mod's: it could swap out their boss or be undone");
        }

        /// <summary>Every method ours and a boss mod both patch; our skipping prefixes there must honour __runOriginal.</summary>
        static void SharedPatches(Action<string> bad, Action<string> note, HashSet<string> theirs)
        {
            try
            {
                int shared = 0;
                foreach (var m in Harmony.GetAllPatchedMethods())
                {
                    var info = Harmony.GetPatchInfo(m);
                    if (info == null) continue;
                    bool ours = false, other = false;
                    foreach (var o in info.Owners) { if (FurtherCore.IsOurHarmonyId(o)) ours = true; else if (theirs.Contains(o)) other = true; }
                    if (!(ours && other)) continue;
                    shared++;
                    bool skips = false;
                    foreach (var p in info.Prefixes) if (theirs.Contains(p.owner) && p.PatchMethod.ReturnType == typeof(bool)) skips = true;
                    note("  shared patch: " + m.DeclaringType.Name + "." + m.Name + (skips ? "  (theirs can skip it)" : ""));
                    foreach (var p in info.Prefixes)
                    {
                        if (!FurtherCore.IsOurHarmonyId(p.owner) || p.PatchMethod.ReturnType != typeof(bool)) continue;
                        bool honours = false;
                        foreach (var a in p.PatchMethod.GetParameters()) if (a.Name == "__runOriginal") honours = true;
                        if (!honours) bad("our prefix " + p.PatchMethod.DeclaringType.Name + " on " + m.DeclaringType.Name + "." + m.Name + " ignores __runOriginal");
                    }
                }
                note("  " + shared + " method(s) patched by both");
            }
            catch (Exception e) { bad("patch overlap scan failed: " + e.Message); }
        }

        static object Prop(object o, string name)
        {
            var p = o != null ? o.GetType().GetProperty(name, BindingFlags.Public | BindingFlags.Instance) : null;
            return p != null ? p.GetValue(o, null) : null;
        }

        static object Field(object o, string name)
        {
            var f = o != null ? o.GetType().GetField(name, BindingFlags.Public | BindingFlags.Instance) : null;
            return f != null ? f.GetValue(o) : null;
        }

        /// <summary>A BepInEx ConfigEntry's value as text ("-" when there is none).</summary>
        static string Entry(object entry)
        {
            var e = entry as BepInEx.Configuration.ConfigEntryBase;
            return e != null && e.BoxedValue != null ? e.BoxedValue.ToString() : "-";
        }
    }
}
