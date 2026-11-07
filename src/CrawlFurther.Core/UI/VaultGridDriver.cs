using System;
using System.Collections.Generic;
using System.Reflection;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.UI
{
    using CrawlFurther.Util;

    /// <summary>Lives on the MenuLibrary object: opens the mod categories, shows their stamps and summaries, and scrolls
    /// grids with the mouse wheel and Page Up / Page Down.</summary>
    public class VaultGridDriver : MonoBehaviour
    {
        MenuLibrary m_lib;
        MenuStateMachine m_states;
        readonly Dictionary<VaultCategory, exSprite> m_stamps = new Dictionary<VaultCategory, exSprite>();
        exSprite m_shownStamp;
        public bool GridMode;
        static MethodInfo s_updatePositions;
        float m_popT = 1f;

        internal void Init(MenuLibrary lib)
        {
            m_lib = lib;
            m_states = GetComponent<MenuStateMachine>();
        }

        /// <summary>One stamp sprite per listed category, where the vanilla stamp sits.</summary>
        internal void MakeStamps()
        {
            var vanilla = R.Get<exSpriteAnimation>(m_lib, "m_spriteStamp");
            if (vanilla == null) return;
            for (int i = VaultGrid.FirstMod; VaultGrid.CategoryOf(i) != null; i++)
            {
                var c = VaultGrid.CategoryOf(i);
                if (m_stamps.ContainsKey(c) || string.IsNullOrEmpty(c.stamp)) continue;
                var sh = Art.SpriteSheets.Get(c.stamp);
                if (sh == null) continue;
                var s = Branding.MakeSprite("Stamp" + c.label, vanilla.transform.parent, sh, vanilla.transform.localPosition);
                s.gameObject.SetActive(false);
                m_stamps[c] = s;
            }
        }

        // SendMessage target of every mod category item: open the one that is selected
        void MsgCategoryMod()
        {
            var c = VaultGrid.CategoryOf(VaultGrid.SelectedLabel(m_lib));
            if (c == null) return;
            try { VaultGrid.Build(m_lib, VaultGrid.NumberOf(c)); }
            catch (Exception e) { FurtherCore.Log.LogError("Vault " + c.label + ": " + e); }
        }

        /// <summary>UpdateCategory postfix: a mod category's summary and stamp while it is the highlighted category.</summary>
        internal void OnUpdateCategory(bool showStamp)
        {
            var c = VaultGrid.CategoryOf(VaultGrid.SelectedLabel(m_lib));
            var summary = R.Get<GUIText>(m_lib, "m_textCategorySummary");
            if (c != null && summary != null && c.summary != null)
            {
                var list = LibraryEntries.EntriesOf(c);
                int found = 0;
                foreach (var e in list)
                    if (c.secrets ? Secrets.IsFound(LibraryEntries.SecretOf(e)) : e.IsFound(string.Empty)) found++;
                summary.gameObject.SetActive(true);
                summary.SetText(c.summary(found, list.Count));
            }
            exSprite want = null;
            if (c != null && showStamp) m_stamps.TryGetValue(c, out want);
            foreach (var kv in m_stamps)
                if (kv.Value != null && kv.Value.gameObject.activeSelf != (kv.Value == want)) kv.Value.gameObject.SetActive(kv.Value == want);
            if (want != null && want != m_shownStamp) m_popT = 0f;
            m_shownStamp = want;
        }

        void Update()
        {
            // a stamp lands with a small press (scale 1.25 -> 1) like the vanilla stamp's flash-in
            if (m_popT < 1f)
            {
                m_popT = Mathf.Min(1f, m_popT + Time.unscaledDeltaTime / 0.15f);
                float k = Mathf.Lerp(1.25f, 1f, m_popT);
                if (m_shownStamp != null && m_shownStamp.gameObject.activeSelf) m_shownStamp.scale = new Vector2(k, k);
            }
            if (m_states == null || m_states.GetStateName() != "Monster") return;
            int rows = 0;
            float wheel = Input.GetAxis("Mouse ScrollWheel");
            if (wheel > 0.01f) rows = -1; else if (wheel < -0.01f) rows = 1;
            if (Input.GetKeyDown(KeyCode.PageDown)) rows = 3;
            if (Input.GetKeyDown(KeyCode.PageUp)) rows = -3;
            if (rows != 0) Scroll(rows);
        }

        void Scroll(int rows)
        {
            try
            {
                var grid = R.Get<MenuTextMenu>(m_lib, "m_menuItemsMonster");
                if (grid == null || !grid.gameObject.activeInHierarchy) return;
                var items = R.Get<List<MenuTextMenuItem>>(grid, "m_items");
                int cols = Mathf.Max(1, R.Get<int>(grid, "m_columns"));
                int maxItems = R.Get<int>(grid, "m_maxItems");
                if (items == null || items.Count == 0 || maxItems <= 0) return;
                int lastRow = (items.Count - 1) / cols;
                int visible = maxItems + 1;
                int off = R.Get<int>(grid, "m_scrollOffset");
                int to = Mathf.Clamp(off + rows, 0, Mathf.Max(0, lastRow - maxItems));
                int sel = Mathf.Max(0, grid.GetSelectedId());
                int col = sel % cols;
                // keep the selection on a middle row of the view (the grid's own keep-visible rule wants it there)
                int selRow = Mathf.Clamp(sel / cols + (to - off), to + (visible > 2 ? 1 : 0), to + visible - (visible > 2 ? 2 : 1));
                if (to == off && sel / cols == selRow) return;
                R.Set(grid, "m_scrollOffset", to);
                if (s_updatePositions == null) s_updatePositions = AccessTools.Method(typeof(MenuTextMenu), "UpdateItemPositions");
                s_updatePositions.Invoke(grid, null);
                int pick = Mathf.Min(items.Count - 1, selRow * cols + col);
                grid.SetSelectedItem(pick);
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Vault scroll: " + e.Message); }
        }
    }
}
