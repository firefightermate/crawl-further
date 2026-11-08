using System;
using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Game
{
    using CrawlFurther.Util;

    /// <summary>
    /// Crawl Chaos: the game mode a continued game turns into, and that the main menu's "Chaos" entry (under Play)
    /// starts from the first floor. What it changes lives with each feature (<see cref="ChaosSpells"/>: two spells).
    /// <para>On from the menu entry until Play is picked again; on from a continue (<see cref="ContinueGame"/>) until the
    /// next game starts. Never in the tutorial, a vault challenge or attract mode.</para>
    /// </summary>
    public static class ChaosMode
    {
        /// <summary>Set false to drop the menu entry and keep continued games as they were.</summary>
        public static bool Enabled = true;

        static bool s_fromMenu, s_fromContinue;

        /// <summary>The game being played is a chaos game.</summary>
        public static bool Active
        {
            get
            {
                if (!Enabled || !(s_fromMenu || s_fromContinue)) return false;
                try
                {
                    if (SystemGame.GetIsTutorialMatch() || SystemTutorial.GetActive()) return false;
                    if (SystemMenu.GetChallengeMode() || SystemMenu.GetAttractMode()) return false;
                }
                catch { return false; }
                return true;
            }
        }

        /// <summary>The game was started from the main menu's Chaos entry.</summary>
        public static bool FromMenu { get { return s_fromMenu; } }

        internal static void OnContinue()
        {
            if (!Enabled || s_fromContinue) return;
            s_fromContinue = true;
            FurtherCore.Log.LogInfo("Chaos: on (the game was continued)");
        }

        internal static void OnGameStart() { s_fromContinue = false; }

        /// <summary>Test mode: chaos on or off for the game being played (as a continue would, until the next game).</summary>
        internal static void SetForThisGame(bool on)
        {
            s_fromContinue = on;
            if (!on) s_fromMenu = false;
        }

        internal static void PickedPlay(bool chaos)
        {
            if (s_fromMenu != chaos) FurtherCore.Log.LogInfo("Chaos: " + (chaos ? "on" : "off") + " from the main menu");
            s_fromMenu = chaos;
        }
    }

    /// <summary>
    /// The main menu's "Chaos" entry, just under Play. It lives on the MenuMain object, where the menu's items send their
    /// messages, and starts a game the way Play does with chaos on.
    /// </summary>
    public class ChaosMenuEntry : MonoBehaviour
    {
        public const string Message = "MsgCrawlModChaos";
        MenuTextMenu m_menu;
        MenuMain m_main;
        bool m_waiting, m_added;
        internal static bool s_fromEntry;

        internal static void Attach(MenuMain main)
        {
            if (main == null || !ChaosMode.Enabled) return;
            var menu = R.Get<MenuTextMenu>(main, "m_menuMain");
            if (menu == null) return;
            var hook = main.GetComponent<ChaosMenuEntry>() ?? main.gameObject.AddComponent<ChaosMenuEntry>();
            hook.m_main = main;
            hook.Bind(menu);
        }

        void Bind(MenuTextMenu menu)
        {
            if (m_menu != menu) { m_menu = menu; m_added = false; m_waiting = false; }
            if (m_added) return;
            if (!R.Get<bool>(menu, "m_initialised"))
            {
                if (!m_waiting) { m_waiting = true; menu.RegisterInitCallback(OnMenuInitialised); }
                return;
            }
            var all = R.Get<List<MenuTextMenuItem>>(menu, "m_itemsAll");
            if (all == null) return;
            int play = -1;
            for (int i = 0; i < all.Count; i++)
            {
                string msg = all[i] != null ? R.Get<string>(all[i], "m_message") : null;
                if (msg == Message) { m_added = true; return; }
                if (msg == "MsgStart" && play < 0) play = i;
            }
            if (play < 0) { FurtherCore.Log.LogWarning("Chaos: the main menu has no Play entry"); return; }
            MenuTextMenuItemData like = null;
            foreach (var d in menu.m_itemsData) if (d != null && d.m_message == "MsgStart") { like = d; break; }
            string label = like != null && !string.IsNullOrEmpty(like.m_text) && like.m_text == like.m_text.ToUpperInvariant() ? "CHAOS" : "Chaos";
            var data = new MenuTextMenuItemData
            {
                m_text = label, m_enabled = true, m_visible = true, m_message = Message,
                m_prefabMenuItem = like != null ? like.m_prefabMenuItem : null,
                m_platforms = like != null ? like.m_platforms : (ePlatform)(-1),
            };
            if (menu.InsertItem(play + 1, data) != null)
            {
                m_added = true;
                FurtherCore.Log.LogInfo("Chaos: main menu entry added under Play");
            }
        }

        void OnMenuInitialised()
        {
            m_waiting = false;
            try { Bind(m_menu); }
            catch (Exception e) { FurtherCore.Log.LogError("Chaos menu entry failed: " + e.Message); }
        }

        // SendMessage target of the entry: Play, with chaos on
        void MsgCrawlModChaos()
        {
            if (m_main == null) m_main = GetComponent<MenuMain>();
            if (m_main == null) return;
            s_fromEntry = true;
            try
            {
                ChaosMode.PickedPlay(true);
                AccessTools.Method(typeof(MenuMain), "MsgStart").Invoke(m_main, null);
            }
            catch (Exception e) { FurtherCore.Log.LogError("Chaos: starting failed: " + e); }
            finally { s_fromEntry = false; }
        }
    }

    [HarmonyPatch(typeof(MenuMain), "Start")]
    static class Patch_ChaosMenuEntry
    {
        static void Postfix(MenuMain __instance)
        {
            try { ChaosMenuEntry.Attach(__instance); }
            catch (Exception e) { FurtherCore.Log.LogWarning("Chaos menu entry: " + e.Message); }
        }
    }

    /// <summary>Play turns chaos off again (the Chaos entry goes through the same method with it on).</summary>
    [HarmonyPatch(typeof(MenuMain), "MsgStart")]
    static class Patch_ChaosPlay
    {
        static void Prefix() { if (!ChaosMenuEntry.s_fromEntry) ChaosMode.PickedPlay(false); }
    }
}
