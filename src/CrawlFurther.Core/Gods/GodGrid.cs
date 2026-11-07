using System;
using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Gods
{
    using CrawlFurther.UI;
    using CrawlFurther.Util;

    /// <summary>
    /// The god list on the god select: Random, every god, Trials and any entries mods append after it (idol slots,
    /// CrawlAPI's Custom), as a grid of pips between the portrait and the starter boxes.
    ///
    /// Vanilla shows two rows that scroll. The grid shows three rows, packed a little tighter and raised by under half a
    /// row, which fits them between the portrait and the boxes without moving anything else. Columns grow with the list
    /// until the pips are as close as they go inside the vanilla width; past that the grid becomes pages of three rows.
    /// Up or down off the edge of a page turns it, and a mouse player turns pages with the wheel or the page arrows.
    /// Item indices never change, so the vanilla select code (and anything patching it) reads them as before.
    /// </summary>
    public class GodGrid : MonoBehaviour
    {
        /// <summary>Rows of pips on screen.</summary>
        public const int Rows = 3;
        const float RowSpacingMult = 0.867f;          // 4.5 -> 3.9 world units
        const float RaiseMult = 0.41f;                // raises the list by 1.85 units
        const float MinColumnSpacingMult = 0.68f;     // a pip and a gap
        const float Parked = 1000f;                   // off-page pips move this far up, out of every hotspot test

        MenuDeitySelectPlayer m_panel;
        MenuTextMenu m_menu;
        List<MenuTextMenuItem> m_items;
        int m_cols0, m_cols = 1, m_count = -1, m_page, m_pages = 1, m_playerId = -1;
        float m_rs0, m_cs0;
        Vector3 m_basePos;
        GameObject m_pageUp, m_pageDown;

        /// <summary>Index of the Trials entry in the god list (the last entry vanilla adds; mod entries follow it).</summary>
        public int TrialsIndex { get; private set; }
        /// <summary>Number of pages (1 while every entry fits on screen).</summary>
        public int PageCount { get { return m_pages; } }

        public static GodGrid Of(MenuDeitySelectPlayer panel) { return panel != null ? panel.GetComponent<GodGrid>() : null; }

        internal static GodGrid Attach(MenuDeitySelectPlayer panel, MenuTextMenu menu)
        {
            var g = panel.GetComponent<GodGrid>() ?? panel.gameObject.AddComponent<GodGrid>();
            if (g.m_menu != null) return g;
            g.m_panel = panel;
            g.m_menu = menu;
            g.m_items = R.Get<List<MenuTextMenuItem>>(menu, "m_items");
            g.m_playerId = R.Get<int>(panel, "m_playerId");
            g.m_cols0 = Mathf.Max(1, R.Get<int>(menu, "m_columns"));
            g.m_rs0 = R.Get<float>(menu, "m_itemSpacing");
            g.m_cs0 = R.Get<float>(menu, "m_columnSpacing");
            g.m_basePos = menu.transform.position;
            // vanilla adds Random, one entry per god that is not a trial, then Trials; count rather than take the last
            // entry, since another mod may already have appended its own
            int gods = 0;
            foreach (var d in SystemDeity.GetDeities()) if (!d.GetIsTrial()) gods++;
            g.TrialsIndex = gods + 1;
            foreach (var f in new[] { "m_arrowUp", "m_arrowDown" })
            {
                var a = R.Get<GameObject>(menu, f);
                if (a != null) { Destroy(a); R.Set(menu, f, null); }
            }
            return g;
        }

        /// <summary>Most columns that fit the vanilla width at the closest spacing.</summary>
        int MaxColumns { get { return m_cols0 > 1 ? Mathf.FloorToInt((m_cols0 - 1) / MinColumnSpacingMult) + 1 : m_cols0; } }

        /// <summary>Lay the grid out for the entries the list has now (runs again by itself when the count changes).</summary>
        public void Layout()
        {
            int total = m_items.Count;
            m_count = total;
            int cols = Mathf.Max(m_cols0, Mathf.Min(Mathf.CeilToInt(total / (float)Rows), MaxColumns));
            float cs = m_cs0;
            if (cols != m_cols0) cs = Mathf.Max(m_cols0 > 1 ? m_cs0 * (m_cols0 - 1) / (cols - 1) : m_cs0, m_cs0 * MinColumnSpacingMult);
            R.Set(m_menu, "m_columnSpacing", cs);
            R.Set(m_menu, "m_columns", cols);
            m_cols = cols;
            int rows = Mathf.CeilToInt(total / (float)cols);
            m_pages = Mathf.Max(1, Mathf.CeilToInt(rows / (float)Rows));
            R.Set(m_menu, "m_maxItems", 0);
            R.Set(m_menu, "m_scrollOffset", 0);
            bool packed = rows >= Rows && m_rs0 > 0f;
            R.Set(m_menu, "m_itemSpacing", packed ? m_rs0 * RowSpacingMult : m_rs0);
            m_menu.transform.position = packed ? m_basePos + Vector3.up * (m_rs0 * RaiseMult) : m_basePos;
            AccessTools.Method(typeof(MenuTextMenu), "UpdateItemPositions").Invoke(m_menu, null);
            m_page = -1;
            ShowPage(PageOf(m_menu.GetSelectedId()));
            FurtherCore.Log.LogInfo(string.Format("God list: {0} entries, {1} cols, {2} rows, {3} page(s), row spacing {4:0.00} -> {5:0.00}, col spacing {6:0.00}",
                total, cols, rows, m_pages, m_rs0, R.Get<float>(m_menu, "m_itemSpacing"), cs));
        }

        int PageOf(int item) { return item < 0 ? 0 : item / m_cols / Rows; }

        void ShowPage(int page)
        {
            page = Mathf.Clamp(page, 0, m_pages - 1);
            if (page == m_page) return;
            m_page = page;
            if (m_pages > 1)
            {
                float rs = R.Get<float>(m_menu, "m_itemSpacing"), cs = R.Get<float>(m_menu, "m_columnSpacing");
                for (int i = 0; i < m_items.Count; i++)
                {
                    var it = m_items[i];
                    int row = i / m_cols;
                    bool on = row / Rows == page;
                    if (it.gameObject.activeSelf != on) it.gameObject.SetActive(on);
                    var p = m_menu.transform.position + new Vector3(cs * (i % m_cols - (m_cols - 1) * 0.5f), -(row - page * Rows) * rs, 0f) + it.GetOffset();
                    it.transform.position = on ? p : p + Vector3.up * Parked;
                }
            }
            PageArrows();
        }

        void PageArrows()
        {
            bool up = m_pages > 1 && m_page > 0, down = m_pages > 1 && m_page < m_pages - 1;
            if ((up || down) && m_pageUp == null)
            {
                var prefab = R.Get<GameObject>(m_menu, "m_prefabArrow");
                if (prefab == null) return;
                var off = (Vector3)R.Get<Vector2>(m_menu, "m_arrowOffset");
                float rs = R.Get<float>(m_menu, "m_itemSpacing");
                m_pageUp = Instantiate(prefab, m_menu.transform.position + off + Vector3.up * rs, Quaternion.identity) as GameObject;
                m_pageDown = Instantiate(prefab, m_menu.transform.position + off - Vector3.up * (rs * Rows), Quaternion.identity) as GameObject;
                m_pageDown.transform.localScale = new Vector3(1f, -1f, 1f);
                m_pageUp.transform.parent = m_menu.transform;
                m_pageDown.transform.parent = m_menu.transform;
            }
            if (m_pageUp != null) m_pageUp.SetActive(up);
            if (m_pageDown != null) m_pageDown.SetActive(down);
        }

        void Update()
        {
            if (m_menu == null) return;
            if (m_items.Count != m_count) { Layout(); return; }
            if (m_pages <= 1) return;
            ShowPage(PageOf(m_menu.GetSelectedId()));
            if (m_menu.isActiveAndEnabled) MouseTurn();
        }

        /// <summary>A mouse player turns pages with the wheel or by clicking a page arrow.</summary>
        void MouseTurn()
        {
            var pd = SystemPlayers.GetPlayer(m_playerId);
            if (pd == null || pd.ControllerId != eController.Mouse) return;
            int dir = 0;
            float w = Input.GetAxis("Mouse ScrollWheel");
            if (Mathf.Abs(w) > 0.01f) dir = w > 0f ? -1 : 1;
            else if (Input.GetMouseButtonDown(0))
            {
                var m = SystemInput.GetMousePos();
                if (Hit(m_pageUp, m)) dir = -1;
                else if (Hit(m_pageDown, m)) dir = 1;
            }
            int target = Mathf.Clamp(m_page + dir, 0, m_pages - 1);
            if (dir == 0 || target == m_page) return;
            m_menu.SetSelectedItem(Mathf.Min(target * Rows * m_cols, m_items.Count - 1));
            ShowPage(target);
        }

        static bool Hit(GameObject arrow, Vector2 p)
        {
            if (arrow == null || !arrow.activeInHierarchy) return false;
            var r = arrow.GetComponent<Renderer>();
            if (r == null) return false;
            var b = r.bounds;
            b.Expand(new Vector3(2f, 2f, 0f));
            return p.x >= b.min.x && p.x <= b.max.x && p.y >= b.min.y && p.y <= b.max.y;
        }
    }

    /// <summary>Builds the god grid once vanilla Start has filled the list, after content appended its entries.</summary>
    [HarmonyPatch(typeof(MenuDeitySelectPlayer), "Start")]
    static class Patch_DeityMenuLayout
    {
        static void Postfix(MenuDeitySelectPlayer __instance)
        {
            try
            {
                var menu = R.Get<MenuTextMenu>(__instance, "m_menu");
                if (menu == null) return;
                var grid = GodGrid.Attach(__instance, menu);
                ModGodPips(__instance, menu);
                Gems(__instance);
                SlotGodBadge.Attach(__instance);
                try { if (SlotGods.AddEntries != null) SlotGods.AddEntries(__instance, menu); }
                catch (Exception e) { FurtherCore.Log.LogError("God list entries: " + e); }
                grid.Layout();
            }
            catch (Exception e) { FurtherCore.Log.LogError("God list layout failed: " + e); }
        }

        /// <summary>The panel's portrait gets the gem whenever it shows mod art: a god, or an origin or ghost form while
        /// a mod's picker shows those in its place. The starter boxes get theirs in Player.SetupPortrait.</summary>
        static void Gems(MenuDeitySelectPlayer panel)
        {
            var portrait = R.Get<exSpriteAnimation>(panel, "m_portrait");
            var spr = portrait != null ? portrait.GetComponent<exSprite>() : null;
            if (spr != null) ModGem.Attach(spr, GemCorner.Cell);
        }

        /// <summary>Gods registered through <see cref="DeityFactory"/> get the violet pip.</summary>
        static void ModGodPips(MenuDeitySelectPlayer panel, MenuTextMenu menu)
        {
            if (DeityFactory.BuiltNames.Count == 0) return;
            var pip = ModIcons.VioletPip(panel);
            if (pip == null) return;
            var all = R.Get<List<MenuTextMenuItem>>(menu, "m_itemsAll");
            int slot = 1;   // item 0 is Random
            foreach (var d in SystemDeity.GetDeities())
            {
                if (d.GetIsTrial()) continue;
                if (DeityFactory.ArtByName.ContainsKey(d.GetName()) && SystemDeity.GetUnlocked(d) && slot < all.Count)
                {
                    var img = all[slot] as MenuItemImage;
                    if (img != null) img.SetAnim(pip);
                }
                slot++;
            }
        }
    }
}
