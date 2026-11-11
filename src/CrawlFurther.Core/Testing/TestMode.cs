using System;
using System.Collections.Generic;
using BepInEx.Configuration;
using UnityEngine;

namespace CrawlFurther.Testing
{
    using CrawlFurther.Compat;
    using CrawlFurther.Diagnostics;

    /// <summary>
    /// Test mode: a panel (F2 by default) for checking content without playing whole runs, plus the game's own hidden
    /// debug menu. Off unless BepInEx/config/CrawlMod.Debug.cfg has [Testing] TestMode = true, and never active in an
    /// online match. Core fills the Become, Spawn, Items, Run, Player, View and Progress pages through the calls below;
    /// any mod can add its own buttons, switches and lists the same way, from its start callback:
    /// <code>
    /// if (TestMode.On)
    /// {
    ///     TestMode.AddAction("My god", "Fill the room with candles", () => MyGod.SpawnCandles(8));
    ///     TestMode.AddToggle("My god", "Endless wax", () => MyGod.EndlessWax, v => MyGod.EndlessWax = v);
    ///     TestMode.AddList("My god", "Become a candle", () => MyGod.Candles.Select(c => new TestItem(c.name, c.prefab)),
    ///         item => TestGame.Become(TestMode.Player, (GameObject)item.Value));
    /// }
    /// </code>
    /// Pages are shown in the order they were first used. An action that throws <see cref="TestModeException"/> shows
    /// its message on the panel; anything else it throws is shown as a failure and logged.
    /// </summary>
    public static class TestMode
    {
        const string ConfigFileName = "CrawlMod.Debug.cfg";
        const float MessageSeconds = 6f;

        static ConfigEntry<bool> s_on;
        static ConfigEntry<KeyCode> s_key;
        static bool s_read, s_started;
        static int s_slot = -1;
        static string s_message;
        static float s_messageAt = -100f;

        internal static readonly List<TestSection> Sections = new List<TestSection>();

        /// <summary>The switch in CrawlMod.Debug.cfg is on (even while an online match keeps the panel shut).</summary>
        public static bool On { get { Read(); return s_on != null && s_on.Value; } }

        /// <summary>This PC is hosting or has joined a Crawl Online session.</summary>
        public static bool Online { get { return CompatOnline.IsHost || CompatOnline.IsClient; } }

        /// <summary>Test mode is on and not blocked by an online match: the panel opens and its actions run.</summary>
        public static bool Active { get { return On && !Online; } }

        /// <summary>The key that opens and closes the panel ([Testing] PanelKey, F2 by default).</summary>
        public static KeyCode PanelKey { get { Read(); return s_key != null ? s_key.Value : KeyCode.F2; } }

        /// <summary>A line for a load banner while test mode is on, or null when it is off.</summary>
        public static string Banner
        {
            get
            {
                if (!On) return null;
                if (Online) return "Test mode is off online";
                return "Test mode on: " + PanelKey + " opens the test panel, Tab + ` the game's debug menu";
            }
        }

        /// <summary>
        /// The player the panel acts for: the one picked at the top of the panel, else the first human monster player,
        /// else the first monster player. Null outside a game.
        /// </summary>
        public static PlayerData Player
        {
            get
            {
                if (!Singleton<SystemPlayers>.HasInstance()) return null;
                if (s_slot >= 0)
                {
                    var picked = SystemPlayers.GetPlayer(s_slot);
                    if (picked != null && picked.IsActive) return picked;
                }
                PlayerData any = null;
                foreach (var p in SystemPlayers.GetPlayers())
                {
                    if (p == null || !p.IsActive || p.IsHero) continue;
                    if (p.IsHuman) return p;
                    if (any == null) any = p;
                }
                return any;
            }
        }

        /// <summary>The player slot picked on the panel, or -1 to follow the default (see <see cref="Player"/>).</summary>
        internal static int Slot { get { return s_slot; } set { s_slot = value; } }

        /// <summary>
        /// Raised when an online match starts while test mode is on: the panel closes and Core's switches go off. Mods
        /// that changed something lasting from a test action put it back here.
        /// </summary>
        public static event Action SwitchedOff;

        internal static void SwitchOff()
        {
            TestCheats.Reset();
            CoreTestActions.Reset();
            if (SwitchedOff == null) return;
            foreach (Action h in SwitchedOff.GetInvocationList())
            {
                try { h(); }
                catch (Exception e) { FurtherCore.Log.LogError("Test mode SwitchedOff handler failed: " + e); }
            }
        }

        /// <summary>Rebuild every list's entries the next time it is drawn (a pick can change what another list shows).</summary>
        internal static void RefreshLists()
        {
            foreach (var s in Sections) foreach (var l in s.Lists) l.Refresh();
        }

        /// <summary>Show a short line at the top of the panel (and in the log).</summary>
        public static void Say(string text)
        {
            s_message = text;
            s_messageAt = Time.unscaledTime;
            FurtherCore.Log.LogInfo("Test mode: " + text);
        }

        /// <summary>The line from <see cref="Say"/> while it is fresh, else null.</summary>
        internal static string Message { get { return Time.unscaledTime - s_messageAt < MessageSeconds ? s_message : null; } }

        /// <summary>Add a button.</summary>
        public static void AddAction(string section, string name, Action run)
        {
            if (!On) return;
            Section(section).Controls.Add(new TestAction { Name = name, Run = run });
        }

        /// <summary>Add an on/off switch that shows <paramref name="get"/> and calls <paramref name="set"/> when clicked.</summary>
        public static void AddToggle(string section, string name, Func<bool> get, Action<bool> set)
        {
            if (!On) return;
            Section(section).Controls.Add(new TestToggle { Name = name, Get = get, Set = set });
        }

        /// <summary>Add a number with - and + buttons and a Go button that calls <paramref name="run"/> with it.</summary>
        public static void AddNumber(string section, string name, int min, int max, int start, Action<int> run)
        {
            if (!On) return;
            Section(section).Controls.Add(new TestNumber { Name = name, Min = min, Max = max, Value = Mathf.Clamp(start, min, max), Run = run });
        }

        /// <summary>Add a row of buttons of which one is lit: <paramref name="get"/> says which, <paramref name="set"/> is told the new one.</summary>
        public static void AddChoice(string section, string name, string[] options, Func<int> get, Action<int> set)
        {
            if (!On) return;
            Section(section).Controls.Add(new TestChoice { Name = name, Options = options, Get = get, Set = set });
        }

        /// <summary>
        /// Add a picker. <paramref name="items"/> is asked for the entries when the panel shows them (and every two
        /// seconds), <paramref name="pick"/> runs when one is clicked. The returned list's Selected is the last pick.
        /// </summary>
        public static TestList AddList(string section, string name, Func<IEnumerable<TestItem>> items, Action<TestItem> pick)
        {
            var list = new TestList(name, items, pick);
            if (On) Section(section).Lists.Add(list);
            return list;
        }

        /// <summary>Run a panel action: refused while test mode is not active, and never lets an exception reach the game.</summary>
        internal static void Run(string what, Action action)
        {
            if (!Active) { Say(Online ? "Test mode is off online" : "Test mode is off"); return; }
            try { action(); }
            catch (TestModeException e) { Say(e.Message); }
            catch (Exception e)
            {
                Say(what + " failed: " + e.Message);
                FurtherCore.Log.LogError("Test mode: " + what + ": " + e);
            }
        }

        static TestSection Section(string name)
        {
            var s = Sections.Find(x => x.Name == name);
            if (s == null) Sections.Add(s = new TestSection(name));
            return s;
        }

        static BepInEx.Configuration.ConfigEntry<bool> s_open;

        /// <summary>Open everything while test mode is on (CrawlMod.Debug.cfg [Testing] OpenEverything). Setting it saves.</summary>
        internal static bool OpenEverything
        {
            get { Read(); return s_open == null || s_open.Value; }
            set { Read(); if (s_open != null) s_open.Value = value; }
        }

        static void Read()
        {
            if (s_read) return;
            s_read = true;
            try
            {
                var cfg = Further.Config(ConfigFileName);
                s_on = cfg.Bind("Testing", "TestMode", false,
                    "Test mode: a panel for trying gods, monsters, items and bosses without playing whole runs, and the " +
                    "game's own debug menu (Tab + `). Off in online matches. Leave off for normal play.");
                s_key = cfg.Bind("Testing", "PanelKey", KeyCode.F2, "The key that opens and closes the test panel.");
                s_open = cfg.Bind("Testing", "OpenEverything", true,
                    "While test mode is on: every god, hero, slot, blob, secret and vault entry (so every monster challenge) " +
                    "reads as open from the moment the game starts. Nothing is written to the save. The test panel's " +
                    "Unlocks page switches it and keeps the choice here.");
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Test mode config: " + e.Message); }
        }

        /// <summary>Called once when the game has booted, before mods start, so Core's pages come first.</summary>
        internal static void Start()
        {
            if (s_started || !On) return;
            s_started = true;
            VanillaDebug.Enable();
            TestPanel.Create();
            CoreTestActions.Register();
            SelfTest.AddSection(2200, "test mode", TestChecks.Run);
            TestCheats.UnlockAll = OpenEverything;
            FurtherCore.Log.LogInfo("Test mode is on: " + PanelKey + " opens the test panel" + (TestCheats.UnlockAll ? "; everything is open" : ""));
        }
    }
}
