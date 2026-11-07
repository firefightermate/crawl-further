using System;
using System.Collections.Generic;
using System.Reflection;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Testing
{
    /// <summary>
    /// The game's own debug mode (SystemDebug), switched on for test mode. Its menu (Tab + `) is filled by systems that
    /// call SystemDebug.AddDebugItem when they start, and only while debugging is already on. SystemUnlocks and
    /// SystemLibrary start before Core can touch the game (the boot wait in FurtherCore), so their items are added here,
    /// each calling the same public game method the game would have; SystemLevel adds its own at every floor start.
    /// The items that write to or wipe the save are labelled so, and the two keys that wipe it are blocked.
    /// </summary>
    static class VanillaDebug
    {
        internal static readonly MethodInfo OnEnabled = AccessTools.Method(typeof(SystemDebug), "OnDebuggingEnabled");
        internal static readonly FieldInfo EnabledField = AccessTools.Field(typeof(SystemDebug), "m_enabled");
        internal static readonly FieldInfo ItemsField = AccessTools.Field(typeof(SystemDebug), "m_menuItems");
        internal static readonly FieldInfo MenuPrefabField = AccessTools.Field(typeof(SystemDebug), "m_prefabDebugMenu");

        const string Writes = " (writes your save)";

        static readonly Dictionary<string, string> s_labels = new Dictionary<string, string>
        {
            { "Unlocks 1. Unlock All", "Unlocks 1. Unlock All" + Writes },
            { "Unlocks 2. Clear Unlocks", "Unlocks 2. Clear Unlocks (erases your unlocks)" },
            { "Unlocks 3. Simulate Unlocks", "Unlocks 3. Simulate Unlocks (erases your unlocks)" },
            { "Library 1. Find All", "Library 1. Find All" + Writes },
            { "Library 2. Find Random 20", "Library 2. Find Random 20" + Writes },
            { "Library 3. Find Weapons", "Library 3. Find Weapons" + Writes },
            { "Library 4. Clear Found Entries", "Library 4. Clear Found Entries (erases your library)" },
        };

        /// <summary>Switch the game's debug mode on and complete its menu. Safe to call more than once.</summary>
        internal static void Enable()
        {
            if (!Singleton<SystemDebug>.HasInstance()) { FurtherCore.Log.LogWarning("Test mode: the game's SystemDebug is missing"); return; }
            var dbg = Singleton<SystemDebug>.Get;
            ClearDevSettings(dbg);
            if (!SystemDebug.Enabled) OnEnabled.Invoke(dbg, null);
            if (Singleton<SystemUnlocks>.HasInstance())
            {
                var u = Singleton<SystemUnlocks>.Get;
                Add("Unlocks", "Unlocks 1. Unlock All", u.DebugUnlockAll);
                Add("Unlocks", "Unlocks 2. Clear Unlocks", u.DebugClearUnlocks);
                Add("Unlocks", "Unlocks 3. Simulate Unlocks", u.DebugPrintUnlockSimulation);
                Add("Unlocks", "Unlocks 4. Print Unlocks", u.DebugPrintUnlocks);
            }
            if (Singleton<SystemLibrary>.HasInstance())
            {
                var l = Singleton<SystemLibrary>.Get;
                Add("Library", "Library 1. Find All", l.DebugFindAll);
                Add("Library", "Library 2. Find Random 20", () => l.DebugFindRandom(20));
                Add("Library", "Library 3. Find Weapons", l.DebugFindAllWeapons);
                Add("Library", "Library 4. Clear Found Entries", l.DebugClearFoundEntries);
            }
            Relabel();
        }

        /// <summary>Pause or resume the game's debug mode without losing its menu (an online match pauses it).</summary>
        internal static void SetActive(bool on)
        {
            if (!Singleton<SystemDebug>.HasInstance() || SystemDebug.Enabled == on) return;
            EnabledField.SetValue(Singleton<SystemDebug>.Get, on);
        }

        /// <summary>Give the save-changing items of the game's menu a warning. SystemLevel re-adds its own each floor;
        /// none of those touch the save.</summary>
        internal static void Relabel()
        {
            var items = Items();
            if (items == null) return;
            foreach (var it in items)
            {
                string label;
                if (it != null && it.m_name != null && s_labels.TryGetValue(it.m_name, out label)) it.m_name = label;
            }
        }

        static List<DebugMenuItem> Items()
        {
            return Singleton<SystemDebug>.HasInstance() ? ItemsField.GetValue(Singleton<SystemDebug>.Get) as List<DebugMenuItem> : null;
        }

        static void Add(string type, string name, Action action)
        {
            var items = Items();
            string label = s_labels.ContainsKey(name) ? s_labels[name] : name;
            if (items == null || items.Exists(i => i != null && (i.m_name == name || i.m_name == label))) return;
            SystemDebug.AddDebugItem(type, label, action);
        }

        /// <summary>
        /// The game's debug object keeps developer settings that only apply while debugging is on (a forced weapon, the
        /// tutorial or challenge mode, achievements without their player rules). None of them belong in a test run.
        /// </summary>
        static void ClearDevSettings(SystemDebug dbg)
        {
            var set = new List<string>();
            if (dbg.m_weaponOverride != null) { set.Add("forced weapon"); dbg.m_weaponOverride = null; }
            if (dbg.m_debugChallengeMode) { set.Add("challenge mode"); dbg.m_debugChallengeMode = false; }
            if (dbg.m_debugChallengeModePlayer != null) { set.Add("challenge player"); dbg.m_debugChallengeModePlayer = null; }
            if (dbg.m_debugTutorialMode) { set.Add("tutorial mode"); dbg.m_debugTutorialMode = false; }
            if (!string.IsNullOrEmpty(dbg.m_startAtTutorialSequence)) { set.Add("tutorial start point"); dbg.m_startAtTutorialSequence = null; }
            if (dbg.m_debugHeroBattle) { set.Add("hero battle"); dbg.m_debugHeroBattle = false; }
            if (dbg.m_debugHeroBattleOverride != null) { set.Add("hero battle scene"); dbg.m_debugHeroBattleOverride = null; }
            if (dbg.m_achievementPlayerReqDisabled) { set.Add("achievement player rules off"); dbg.m_achievementPlayerReqDisabled = false; }
            if (set.Count > 0) FurtherCore.Log.LogInfo("Test mode: cleared the game's debug settings: " + string.Join(", ", set.ToArray()));
        }

        /// <summary>Tab + Delete deletes every save and Tab + Shift + U clears every unlock: never from test mode.</summary>
        internal static bool WipeKeyDown()
        {
            if (!Input.GetKey(KeyCode.Tab)) return false;
            return Input.GetKeyDown(KeyCode.Delete) || (Input.GetKeyDown(KeyCode.U) && Input.GetKey(KeyCode.LeftShift));
        }
    }
}
