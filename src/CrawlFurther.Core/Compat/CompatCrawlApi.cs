using System;
using System.Collections.Generic;
using System.Reflection;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Compat
{
    using CrawlFurther.Gods;
    using CrawlFurther.Util;

    /// <summary>
    /// CrawlAPI compatibility (Anumania's CrawlAPI, plugin GUID org.anumania.plugins.crawlapi). Reflection only: no
    /// compile-time reference, and nothing here runs when CrawlAPI is not loaded.
    ///
    /// What CrawlAPI does to the god select, with MonoMod hooks: its MenuDeitySelectPlayer.Start hook runs the original
    /// Start and then appends a "Custom" entry (message MsgOnSelectModDeities) after everything in the list; an IL hook
    /// on Update makes vanilla read the second-to-last entry as Trials instead of the last; its Update hook, after the
    /// original, draws "Custom" while the last entry is selected and, in its own DeityModdedSelect menu state, calls
    /// SetDeity with the god picked from DeityAPI.customDeities.
    ///
    /// Why that breaks with Core: content appends its own entries after Trials (the idol slots), so Trials is no longer
    /// second to last; and while Custom is selected, vanilla Update reads it as a god and calls SetDeity on whatever
    /// deity sits at that index (a trial god, or null), every frame, against CrawlAPI's own SetDeity.
    ///
    /// What Core does, keeping CrawlAPI's Custom entry and its menu reachable:
    /// <list type="bullet">
    /// <item>The god grid lays itself out again when the entry count changes, so the Custom entry, added after Core's
    /// layout, joins the grid (GodGrid.Update).</item>
    /// <item>An Update prefix (only while CrawlAPI is loaded) answers the entries vanilla would misread: Trials (by its
    /// real index), the god at count - 2 (which the IL hook takes for Trials), Custom (vanilla is skipped and the panel
    /// is reset once on entering it, so the next god redraws), and any other mod entry after Trials (vanilla is
    /// skipped). It leaves alone a frame another prefix already took (the idol slots, the origin page).</item>
    /// <item>Its deities stay in its own Custom menu; they are not folded into the grid.</item>
    /// </list>
    /// </summary>
    public static class CompatCrawlApi
    {
        /// <summary>CrawlAPI's plugin GUID.</summary>
        public const string Guid = "org.anumania.plugins.crawlapi";
        /// <summary>The message of CrawlAPI's Custom entry in the god list.</summary>
        public const string CustomMessage = "MsgOnSelectModDeities";

        static bool s_resolved;
        static Assembly s_asm;
        static FieldInfo f_customDeities;
        static readonly FieldInfo f_message = AccessTools.Field(typeof(MenuTextMenuItem), "m_message");
        static readonly Dictionary<int, int> s_lastSel = new Dictionary<int, int>();

        /// <summary>CrawlAPI is loaded.</summary>
        public static bool Present { get { Resolve(); return s_asm != null; } }

        static void Resolve()
        {
            if (s_resolved) return;
            s_resolved = true;
            try
            {
                BepInEx.PluginInfo info;
                if (!BepInEx.Bootstrap.Chainloader.PluginInfos.TryGetValue(Guid, out info) || info == null || info.Instance == null) return;
                s_asm = info.Instance.GetType().Assembly;
                var api = s_asm.GetType("CrawlAPI.DeityAPI", false);
                f_customDeities = api != null ? api.GetField("customDeities", BindingFlags.Public | BindingFlags.Static) : null;
                FurtherCore.Log.LogInfo("CrawlAPI " + info.Metadata.Version + " detected: god select compatibility on");
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("CrawlAPI compat: " + e.Message); }
        }

        /// <summary>The gods CrawlAPI holds (DeityAPI.customDeities); empty when it is not loaded.</summary>
        public static List<Deity> CustomDeities
        {
            get
            {
                Resolve();
                try { return (f_customDeities != null ? f_customDeities.GetValue(null) as List<Deity> : null) ?? new List<Deity>(); }
                catch { return new List<Deity>(); }
            }
        }

        /// <summary>Index of CrawlAPI's Custom entry in a god list, or -1.</summary>
        public static int CustomIndex(MenuTextMenu menu)
        {
            var items = R.Get<List<MenuTextMenuItem>>(menu, "m_items");
            for (int i = items.Count - 1; i >= 0; i--)
                if (items[i] != null && f_message.GetValue(items[i]) as string == CustomMessage) return i;
            return -1;
        }

        static readonly MethodInfo m_setTrials = AccessTools.Method(typeof(MenuDeitySelectPlayer), "SetTrialsDeity");
        static readonly MethodInfo m_setDeity = AccessTools.Method(typeof(MenuDeitySelectPlayer), "SetDeity");

        /// <summary>The Update prefix's work: true lets vanilla run.</summary>
        internal static bool PanelUpdate(MenuDeitySelectPlayer panel)
        {
            var trials = R.Get<MenuTextMenu>(panel, "m_menuTrials");
            if (trials != null && trials.gameObject.activeSelf) return true;   // the trials list: vanilla reads it right
            var menu = R.Get<MenuTextMenu>(panel, "m_menu");
            var grid = GodGrid.Of(panel);
            if (menu == null || grid == null) return true;
            int sel = menu.GetSelectedId(), count = menu.GetItemCount(), custom = CustomIndex(menu);
            int key = panel.GetInstanceID(), last;
            bool entered = !s_lastSel.TryGetValue(key, out last) || last != sel;
            s_lastSel[key] = sel;
            bool listShown = menu.gameObject.activeInHierarchy;
            if (sel == custom)
            {
                // CrawlAPI draws this entry (and its own menu) after the original; reset once so the next god redraws
                if (entered && listShown) ResetPanel(panel);
                if (listShown) Arrows(panel, menu);
                return false;
            }
            if (sel > grid.TrialsIndex) return false;                          // another mod's entry: its owner draws it
            if (!listShown) return true;
            if (sel == grid.TrialsIndex)
            {
                m_setTrials.Invoke(panel, null);
                Arrows(panel, menu);
                return false;
            }
            if (sel > 0 && sel == count - 2)
            {
                m_setDeity.Invoke(panel, new object[] { SystemDeity.GetDeity(sel - 1), true });
                Arrows(panel, menu);
                return false;
            }
            return true;
        }

        static void ResetPanel(MenuDeitySelectPlayer panel)
        {
            R.Set(panel, "m_deity", null);
            var tf = AccessTools.Field(typeof(MenuDeitySelectPlayer), "m_selectedItemType");
            tf.SetValue(panel, Enum.ToObject(tf.FieldType, 0));
        }

        static void Arrows(MenuDeitySelectPlayer panel, MenuTextMenu menu)
        {
            var l = R.Get<GameObject>(panel, "m_arrowL");
            var r = R.Get<GameObject>(panel, "m_arrowR");
            if (l != null) l.SetActive(menu.HasPrevColumn());
            if (r != null) r.SetActive(menu.HasNextColumn());
        }

        // ---------------------------------------------------------------- self-test
        /// <summary>Self-test section: what was found and what to check by hand.</summary>
        public static void SelfCheck(Action<string> bad, Action<string> note)
        {
            Resolve();
            if (s_asm == null) { note("CrawlAPI not installed: nothing to check"); return; }
            note("CrawlAPI found (" + s_asm.GetName().Name + "), " + CustomDeities.Count + " custom deities");
            if (f_customDeities == null) bad("CrawlAPI.DeityAPI.customDeities not found: its gods cannot be listed");
            if (f_message == null) bad("MenuTextMenuItem.m_message not found: the Custom entry cannot be recognised");
            if (m_setTrials == null || m_setDeity == null) bad("MenuDeitySelectPlayer.SetTrialsDeity / SetDeity not found");
            var update = AccessTools.Method(typeof(MenuDeitySelectPlayer), "Update");
            var info = update != null ? Harmony.GetPatchInfo(update) : null;
            bool ours = false;
            if (info != null) foreach (var p in info.Prefixes) if (p.PatchMethod.DeclaringType == typeof(Patch_CrawlApiDeityUpdate)) ours = true;
            if (!ours) bad("the god select Update prefix for CrawlAPI is not in");
            note("  check by hand: the Custom entry is the last pip and shows \"Custom\"; Trials and the god before it read right;");
            note("  confirming Custom opens CrawlAPI's list and picking a god there starts with it");
        }
    }

    /// <summary>With CrawlAPI loaded: the god list entries vanilla Update would misread (see <see cref="CompatCrawlApi"/>).</summary>
    [HarmonyPatch(typeof(MenuDeitySelectPlayer), "Update")]
    static class Patch_CrawlApiDeityUpdate
    {
        static bool Prepare() { return CompatCrawlApi.Present; }

        static bool Prefix(MenuDeitySelectPlayer __instance, bool __runOriginal)
        {
            if (!__runOriginal) return false;
            try { return CompatCrawlApi.PanelUpdate(__instance); }
            catch (Exception e) { FurtherCore.Log.LogWarning("CrawlAPI god select: " + e.Message); return true; }
        }
    }
}
