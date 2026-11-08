using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace CrawlFurther.Diagnostics
{
    using CrawlFurther.Compat;
    using CrawlFurther.Ghosts;
    using CrawlFurther.UI;

    /// <summary>
    /// Checks everything the packs built, once, right after they register, and writes the report to
    /// CrawlMod_selftest.txt in Core's plugin folder (the banner shows the problem count). Any mod can add a section:
    /// <code>
    /// SelfTest.AddSection(3000, "my god", () =>
    /// {
    ///     if (SystemDeity.GetDeity("MyGod") == null) SelfTest.Bad("MyGod is not registered");
    ///     SelfTest.Note("MyGod: 4 starters");
    /// });
    /// </code>
    /// </summary>
    public static class SelfTest
    {
        class Entry { public int order, seq; public string name; public Action check; }

        static readonly List<Entry> s_sections = new List<Entry>();
        static StringBuilder s_sb;
        static int s_problems;
        static bool s_coreAdded;

        /// <summary>
        /// Add a section. Sections run by <paramref name="order"/> (ties in the order they were added). Core's own use
        /// 100 (monsters), 200 (menu pictures), 1200 (branding), 1300 (vault grid), 1310 (vault challenges), 1400 (ghost button controls),
        /// 2000 (online), 2050 (CrawlAPI), 2060 (boss mods), 2100 (Harmony patch classes) and, while test mode is on, 2200 (test mode). A section that throws is reported as a problem and the
        /// others still run. Add sections from your start callback or your packs.
        /// </summary>
        public static void AddSection(int order, string name, Action check)
        {
            s_sections.Add(new Entry { order = order, seq = s_sections.Count, name = name, check = check });
        }

        /// <summary>Report a problem: counted, and listed under the running section. Call it only from inside a section.</summary>
        public static void Bad(string msg)
        {
            if (s_sb == null) { FurtherCore.Log.LogWarning("SelfTest.Bad outside a section: " + msg); return; }
            s_problems++;
            s_sb.AppendLine("  PROBLEM: " + msg);
        }

        /// <summary>Write a line to the report. Call it only from inside a section.</summary>
        public static void Note(string msg)
        {
            if (s_sb != null) s_sb.AppendLine(msg);
        }

        static void AddCoreSections()
        {
            if (s_coreAdded) return;
            s_coreAdded = true;
            AddSection(10, "mods started", () =>
            {
                // a mod whose start threw registers nothing; say so first instead of passing an empty mod
                foreach (var f in FurtherCore.FailedStarts) Bad("mod failed to start: " + f);
                foreach (var f in ContentManager.FailedPacks) Bad("pack failed to register: " + f);
            });
            AddSection(100, "monsters", MonsterChecks.CheckMonsters);
            AddSection(200, "menu pictures", MonsterChecks.CheckPictures);
            AddSection(1200, "branding", () => Branding.SelfCheck(Bad));
            AddSection(1300, "vault grid", () => VaultGrid.SelfCheck(Bad));
            AddSection(1310, "vault challenges", () => LibraryEntries.ChallengeSelfCheck(Bad, Note));
            AddSection(1400, "ghost button controls", () => GhostControls.SelfCheck(Bad));
            AddSection(1450, "continue after a win", () => Game.ContinueGame.SelfCheck(Bad, Note));
            AddSection(2000, "online (Crawl Online compatibility)", () => CompatOnline.SelfCheck(Bad, Note));
            AddSection(2050, "CrawlAPI compatibility", () => CompatCrawlApi.SelfCheck(Bad, Note));
            AddSection(2060, "boss mods (CrawlCustomBosses and others)", () => CompatBosses.SelfCheck(Bad, Note));
            AddSection(2100, "harmony patch classes", CheckPatchClasses);
        }

        /// <summary>
        /// Run every patch class's static setup now: one that throws (an ambiguous reflection lookup, say) would otherwise
        /// throw TypeInitializationException from inside the patched game method on every call.
        /// </summary>
        static void CheckPatchClasses()
        {
            // a patch that did not go in is only in the log otherwise: its feature is silently off
            foreach (var f in FurtherCore.FailedPatches) Bad("patch failed to apply: " + f);
            int n = 0;
            foreach (var asm in FurtherCore.Assemblies)
                foreach (var t in asm.GetTypes())
                {
                    if (t.GetCustomAttributes(typeof(HarmonyLib.HarmonyPatch), false).Length == 0) continue;
                    n++;
                    try { System.Runtime.CompilerServices.RuntimeHelpers.RunClassConstructor(t.TypeHandle); }
                    catch (Exception e) { Bad("patch " + t.Name + " static setup throws: " + (e.InnerException ?? e).Message); }
                }
            Note("  " + n + " patch classes initialised");
        }

        internal static void Run()
        {
            s_sb = new StringBuilder();
            s_problems = 0;
            Note(Branding.DisplayName + " self-test " + DateTime.Now + "  (v" + Branding.Version + ")");

            AddCoreSections();
            var order = new List<Entry>(s_sections);
            order.Sort((x, y) => x.order != y.order ? x.order.CompareTo(y.order) : x.seq.CompareTo(y.seq));
            foreach (var e in order) Section(e.name, e.check);

            Note(s_problems == 0 ? "ALL CHECKS PASSED" : s_problems + " problem(s)");
            try { File.WriteAllText(Path.Combine(FurtherCore.ModDir, "CrawlMod_selftest.txt"), s_sb.ToString()); } catch { }
            FurtherCore.Log.LogInfo("Self-test: " + (s_problems == 0 ? "all checks passed" : s_problems + " problem(s), see CrawlMod_selftest.txt"));
            ContentManager.Status += s_problems == 0 ? "  self-test OK" : "  self-test: " + s_problems + " problem(s)";
            s_sb = null;
        }

        static void Section(string name, Action check)
        {
            Note("== " + name);
            try { check(); }
            catch (Exception e)
            {
                Bad("self-test section '" + name + "' crashed: " + e.GetType().Name + ": " + e.Message);
                FurtherCore.Log.LogError("Self-test " + name + ": " + e);
            }
        }
    }
}
