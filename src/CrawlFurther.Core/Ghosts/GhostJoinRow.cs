using System;
using System.Collections.Generic;
using HarmonyLib;
using InControl;
using UnityEngine;

namespace CrawlFurther.Ghosts
{
    using CrawlFurther.Compat;
    using CrawlFurther.UI;
    using CrawlFurther.Util;

    /// <summary>The GHOST row on a join-screen player's Controls page (on the MenuJoinOptions object: it receives the
    /// row's message).</summary>
    public class GhostJoinRow : MonoBehaviour
    {
        public const string Msg = "MsgGhostButton";
        MenuJoinOptions m_join;
        internal bool m_pending;
        int m_shownCid = -1;

        public static GhostJoinRow Ensure(MenuJoinOptions j)
        {
            var row = j.GetComponent<GhostJoinRow>() ?? j.gameObject.AddComponent<GhostJoinRow>();
            row.m_join = j;
            var menu = row.Menu;
            if (menu == null || menu.m_itemsData.Exists(d => d != null && d.m_message == Msg)) return row;
            var data = new MenuTextMenuItemData { m_text = "Ghost:C", m_enabled = true, m_visible = true, m_message = Msg };
            int at = menu.m_itemsData.FindIndex(d => d != null && d.m_message == "MsgControlsBack");
            if (at < 0) at = menu.m_itemsData.Count;
            if (R.Get<bool>(menu, "m_initialised"))
            {
                // not expected (the page builds its rows after this object's OnEnable), but keep the row order
                FurtherCore.Log.LogWarning("Ghost button: the Controls page was already built, inserting the row late");
                menu.m_itemsData.Insert(at, data);
                var item = menu.InsertItem(at, data);
                if (item != null) item.transform.localScale = Vector3.one;
            }
            else menu.m_itemsData.Insert(at, data);
            return row;
        }

        MenuTextMenu Menu { get { return m_join != null ? R.Get<MenuTextMenu>(m_join, "m_menuControls") : null; } }
        MenuStateMachine States { get { return m_join != null ? R.Get<MenuStateMachine>(m_join, "m_states") : null; } }
        int Index { get { var m = Menu; return m != null ? m.m_itemsData.FindIndex(d => d != null && d.m_message == Msg) : -1; } }

        PlayerData Player()
        {
            try { return m_join != null ? SystemPlayers.GetPlayer(R.Get<int>(m_join, "m_playerId")) : null; }
            catch { return null; }
        }

        int Cid()
        {
            var pd = Player();
            return pd != null && pd.IsActive ? (int)pd.ControllerId : -1;
        }

        // an online player's pad (Crawl Online): their ghost button is set on their own PC, so no row here
        static bool Settable(int cid) { return GhostControls.IsKeyboard(cid) || (GhostControls.IsPad(cid) && !CompatOnline.IsRemotePad(cid)); }

        /// <summary>The row's message: listen for a new ghost button, in the REDEFINE panel.</summary>
        void MsgGhostButton()
        {
            var st = States;
            if (st == null || !Settable(Cid())) return;
            m_pending = true;
            st.SetState("InputBinding");
        }

        internal void Listen()
        {
            int cid = Cid();
            var st = States;
            var l = GhostBindListener.For(R.Get<MenuInputBinding>(m_join, "m_menuInputBinding"));
            if (l == null || st == null || !Settable(cid)) { if (st != null) st.SetState("Controls"); return; }
            GhostControls.ClearMoved(cid);
            l.Begin(cid, null, false, ok =>
            {
                if (st != null) st.SetState("Controls");
                Refresh();
            });
        }

        public void Refresh()
        {
            var menu = Menu;
            int i = Index;
            if (menu == null || i < 0) return;
            int cid = Cid();
            bool show = Settable(cid);
            menu.SetItemVisible(i, show);
            if (!show) return;
            m_shownCid = cid;
            string text = RowText(cid);
            menu.SetItemString(i, text);
            var all = R.Get<List<MenuTextMenuItem>>(menu, "m_itemsAll");
            if (all != null && i < all.Count) Fit(all[i], text, RowWidth);
        }

        /// <summary>A join panel row's room in font pixels (the panel is 50 units, a row's font 1 unit a pixel; vanilla's
        /// widest rows, "Aim:Smooth" and "AI: Normal", are 37 and 33).</summary>
        public const int RowWidth = 44;

        /// <summary>"Ghost:C", or "Ghost now:V" after a rebind moved it (when that still fits a panel row).</summary>
        public static string RowText(int cid)
        {
            string name = GhostControls.NameOf(cid);
            string moved = "Ghost now:" + name;
            return GhostControls.Moved(cid) && PauseTips.Width(moved) <= RowWidth ? moved : "Ghost:" + name;
        }

        /// <summary>Shrink a row's font (selected or not) so a long button name stays inside the panel.</summary>
        public static void Fit(MenuTextMenuItem item, string text, int room)
        {
            if (item == null) return;
            int w = PauseTips.Width(text);
            float k = w > room ? Mathf.Max(0.6f, room / (float)w) : 1f;
            R.Set(item, "m_textSize", k);
            R.Set(item, "m_textSizeSelected", k);
            var g = R.Get<GUIText>(item, "m_textComponent");
            if (g != null) g.SetFontScale(k);
        }

        /// <summary>Open the Controls page on the GHOST row (a Redefine just moved the ghost button).</summary>
        internal void ShowMoved()
        {
            var st = States;
            var menu = Menu;
            if (st == null || menu == null) return;
            st.SetState("Controls");
            Refresh();
            var items = R.Get<List<MenuTextMenuItem>>(menu, "m_items");
            var all = R.Get<List<MenuTextMenuItem>>(menu, "m_itemsAll");
            int i = Index;
            if (items != null && all != null && i >= 0 && i < all.Count)
            {
                int k = items.IndexOf(all[i]);
                if (k >= 0) menu.SetSelectedItem(k);
            }
        }

        void OnDisable()
        {
            m_pending = false;
            if (m_shownCid >= 0) GhostControls.ClearMoved(m_shownCid);
        }
    }

    [HarmonyPatch(typeof(MenuJoinOptions), "OnEnable")]
    static class Patch_GhostJoinRowAdd
    {
        static void Prefix(MenuJoinOptions __instance)
        {
            try { GhostJoinRow.Ensure(__instance); }
            catch (Exception e) { FurtherCore.Log.LogWarning("Ghost button row (join): " + e.Message); }
        }
    }

    [HarmonyPatch(typeof(MenuJoinOptions), "OnEnterState")]
    static class Patch_GhostJoinListen
    {
        static bool Prefix(MenuJoinOptions __instance)
        {
            try
            {
                var row = __instance.GetComponent<GhostJoinRow>();
                var st = R.Get<MenuStateMachine>(__instance, "m_states");
                if (row == null || st == null) return true;
                bool binding = st.GetStateName() == "InputBinding";
                if (binding && row.m_pending)
                {
                    row.m_pending = false;
                    row.Listen();
                    return false;                     // not vanilla's Redefine
                }
                row.m_pending = false;
                if (binding) GhostControls.Watch();    // vanilla's Redefine: remember the ghost buttons it may move
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Ghost button listen (join): " + e.Message); }
            return true;
        }
    }

    [HarmonyPatch(typeof(MenuJoinOptions), "UpdateItemTextControls")]
    static class Patch_GhostJoinRowText
    {
        static void Postfix(MenuJoinOptions __instance)
        {
            try { var row = __instance.GetComponent<GhostJoinRow>(); if (row != null) row.Refresh(); }
            catch (Exception e) { FurtherCore.Log.LogWarning("Ghost button row text (join): " + e.Message); }
        }
    }

    /// <summary>The page's Reset (vanilla's per player reset) resets the ghost button too.</summary>
    [HarmonyPatch(typeof(MenuJoinOptions), "MsgControlsReset")]
    static class Patch_GhostJoinReset
    {
        static void Prefix() { try { GhostControls.Watch(); } catch { } }

        static void Postfix(MenuJoinOptions __instance)
        {
            try
            {
                var pd = SystemPlayers.GetPlayer(R.Get<int>(__instance, "m_playerId"));
                if (pd != null) GhostControls.Reset((int)pd.ControllerId);   // after vanilla's reset: its own row reads plain
                GhostControls.Changed();
                var row = __instance.GetComponent<GhostJoinRow>();
                if (row != null) row.Refresh();
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Ghost button reset (join): " + e.Message); }
        }
    }

    /// <summary>After vanilla's Redefine: if it took the ghost button, open the Controls page on the moved GHOST row.</summary>
    [HarmonyPatch(typeof(MenuJoinOptions), "OnControlsRedefineComplete")]
    static class Patch_GhostJoinAfterRedefine
    {
        static void Postfix(MenuJoinOptions __instance)
        {
            try
            {
                GhostControls.Changed();
                var row = __instance.GetComponent<GhostJoinRow>();
                var st = R.Get<MenuStateMachine>(__instance, "m_states");
                var pd = SystemPlayers.GetPlayer(R.Get<int>(__instance, "m_playerId"));
                if (row == null || st == null || pd == null) return;
                int cid = (int)pd.ControllerId;
                if (GhostControls.Moved(cid) && st.GetStateName() == "Options") row.ShowMoved();
                else row.Refresh();
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Ghost button after redefine (join): " + e.Message); }
        }
    }
}
