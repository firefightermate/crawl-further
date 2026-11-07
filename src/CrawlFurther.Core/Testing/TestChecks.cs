using System.Reflection;
using HarmonyLib;

namespace CrawlFurther.Testing
{
    using CrawlFurther.Diagnostics;

    /// <summary>Self-test section (only while test mode is on): every game member the panel calls resolves, the game's
    /// debug mode is on with its menu, and each test hook is patched.</summary>
    static class TestChecks
    {
        internal static void Run()
        {
            Need("SystemDebug.OnDebuggingEnabled", VanillaDebug.OnEnabled);
            Need("SystemDebug.m_enabled", VanillaDebug.EnabledField);
            Need("SystemDebug.m_menuItems", VanillaDebug.ItemsField);
            Need("SystemDebug.m_prefabDebugMenu", VanillaDebug.MenuPrefabField);
            foreach (var kv in TestGame.Hooks()) Need(kv.Key, kv.Value);

            if (!Singleton<SystemDebug>.HasInstance()) SelfTest.Bad("the game has no SystemDebug: its debug menu is unavailable");
            else
            {
                var dbg = Singleton<SystemDebug>.Get;
                if (VanillaDebug.MenuPrefabField != null && VanillaDebug.MenuPrefabField.GetValue(dbg) == null)
                    SelfTest.Bad("SystemDebug has no debug menu prefab: Tab + ` will not open anything");
                if (!SystemDebug.Enabled && !TestMode.Online) SelfTest.Bad("the game's debug mode did not switch on");
                var items = VanillaDebug.ItemsField != null ? VanillaDebug.ItemsField.GetValue(dbg) as System.Collections.ICollection : null;
                SelfTest.Note("game debug menu: " + (items != null ? items.Count + " items before the first floor" : "unreadable"));
            }

            Patched("SystemMain.UpdateDebugKeys", AccessTools.Method(typeof(SystemMain), "UpdateDebugKeys"));
            Patched("SystemUnlocks.GetLocked(string)", AccessTools.Method(typeof(SystemUnlocks), "GetLocked", new[] { typeof(string) }));
            Patched("SystemLibrary.OnEntryFound", AccessTools.Method(typeof(SystemLibrary), "OnEntryFound",
                new[] { typeof(PlayerData), typeof(UnityEngine.GameObject), typeof(string) }));
            Patched("PlayerAI.Update", AccessTools.Method(typeof(PlayerAI), "Update"));
            Patched("PlayerAI.GetMoveRatio", AccessTools.Method(typeof(PlayerAI), "GetMoveRatio"));
            Patched("PlayerAI.GetAttackToStart", AccessTools.Method(typeof(PlayerAI), "GetAttackToStart"));
            Patched("Bot.Update", AccessTools.Method(typeof(Bot), "Update"));
            Patched("PlayerBotData.GetInputMove", AccessTools.Method(typeof(PlayerBotData), "GetInputMove"));

            if (!TestPanel.Exists) SelfTest.Bad("the test panel object was not created");
            int controls = 0, lists = 0;
            foreach (var s in TestMode.Sections) { controls += s.Controls.Count; lists += s.Lists.Count; }
            SelfTest.Note("test panel: " + TestMode.Sections.Count + " pages, " + controls + " controls, " + lists + " lists; key " + TestMode.PanelKey);
        }

        static void Need(string what, MemberInfo m)
        {
            if (m == null) SelfTest.Bad("test mode: game member not found: " + what);
        }

        static void Patched(string what, MethodBase target)
        {
            if (target == null) { SelfTest.Bad("test mode: hook target not found: " + what); return; }
            var info = Harmony.GetPatchInfo(target);
            bool ours = false;
            if (info != null)
                foreach (var owner in info.Owners) if (owner == FurtherCore.GUID) ours = true;
            if (!ours) SelfTest.Bad("test mode: " + what + " is not patched");
        }
    }
}
