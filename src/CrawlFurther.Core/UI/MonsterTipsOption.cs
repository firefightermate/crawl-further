using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.UI
{
    using CrawlFurther.Util;

    /// <summary>
    /// Lives on the MenuOptions object, which is where the menu items send their messages. Two items at the end of the
    /// options list, one after the other: "Tips: ALL / P1 ONLY / OFF" (who sees tips) and "Tooltips: ALWAYS / FIRST TIME /
    /// OFF" (when). The list scrolls (it shows 5 rows), so the extra rows take their own place below "Easter Eggs".
    /// </summary>
    public class MonsterTipsOption : MonoBehaviour
    {
        public const string Message = "MsgCrawlModMonsterTips", MessageTooltips = "MsgCrawlModTooltips";
        MenuTextMenu m_menu;
        int m_index = -1, m_indexTooltips = -1;
        bool m_waiting;

        public static void Attach(MenuOptions options)
        {
            if (options == null) return;
            var menu = R.Get<MenuTextMenu>(options, "m_menuOptions");
            if (menu == null) return;
            var hook = options.GetComponent<MonsterTipsOption>();
            if (hook == null) hook = options.gameObject.AddComponent<MonsterTipsOption>();
            hook.Bind(menu);
        }

        static string Label()
        {
            switch (MonsterTips.TipsFor)
            {
                case MonsterTips.Mode.P1: return "Tips: P1 ONLY";
                case MonsterTips.Mode.Off: return "Tips: OFF";
            }
            return "Tips: ALL";
        }

        static string LabelTooltips()
        {
            switch (MonsterTips.Tooltips)
            {
                case MonsterTips.Repeat.FirstTime: return "Tooltips: FIRST TIME";
                case MonsterTips.Repeat.Off: return "Tooltips: OFF";
            }
            return "Tooltips: ALWAYS";
        }

        static int Find(List<MenuTextMenuItem> all, string message)
        {
            for (int i = 0; i < all.Count; i++)
                if (all[i] != null && R.Get<string>(all[i], "m_message") == message) return i;
            return -1;
        }

        int Add(MenuTextMenu menu, List<MenuTextMenuItem> all, string message, string label)
        {
            var item = menu.AddItem(MakeData(menu, message, label));
            int index = item != null ? all.IndexOf(item) : -1;
            if (index >= 0) FurtherCore.Log.LogInfo("Monster tips: options item " + message + " added (" + all.Count + " items)");
            return index;
        }

        void Bind(MenuTextMenu menu)
        {
            if (menu == null) return;
            if (m_menu != menu) { m_menu = menu; m_index = -1; m_indexTooltips = -1; m_waiting = false; }
            if (m_index < 0 || m_indexTooltips < 0)
            {
                if (!R.Get<bool>(menu, "m_initialised"))
                {
                    // its items are built in its Start: add ours right after
                    if (!m_waiting) { m_waiting = true; menu.RegisterInitCallback(OnMenuInitialised); }
                    return;
                }
                var all = R.Get<List<MenuTextMenuItem>>(menu, "m_itemsAll");
                m_index = Find(all, Message);
                if (m_index < 0) m_index = Add(menu, all, Message, Label());
                m_indexTooltips = Find(all, MessageTooltips);
                if (m_indexTooltips < 0) m_indexTooltips = Add(menu, all, MessageTooltips, LabelTooltips());
            }
            if (m_index >= 0) menu.SetItemString(m_index, Label());
            if (m_indexTooltips >= 0) menu.SetItemString(m_indexTooltips, LabelTooltips());
        }

        void OnMenuInitialised()
        {
            m_waiting = false;
            try { Bind(m_menu); }
            catch (Exception e) { FurtherCore.Log.LogError("Monster tips option failed: " + e.Message); }
        }

        static MenuTextMenuItemData MakeData(MenuTextMenu menu, string message, string label)
        {
            // copy the plain ON/OFF toggle look of "Game Tips"
            MenuTextMenuItemData like = null;
            foreach (var d in menu.m_itemsData)
                if (d != null && (d.m_message == "MsgTutorial" || (like == null && d.m_message == "MsgFlicker"))) { like = d; if (d.m_message == "MsgTutorial") break; }
            return new MenuTextMenuItemData
            {
                m_text = label,
                m_enabled = true,
                m_visible = true,
                m_message = message,
                m_prefabMenuItem = like != null ? like.m_prefabMenuItem : null,
                m_platforms = like != null ? like.m_platforms : (ePlatform)(-1),
            };
        }

        // SendMessage target of our menu item
        void MsgCrawlModMonsterTips()
        {
            // ALL, then P1 ONLY, then OFF, then ALL again
            MonsterTips.TipsFor = MonsterTips.TipsFor == MonsterTips.Mode.All ? MonsterTips.Mode.P1
                                : MonsterTips.TipsFor == MonsterTips.Mode.P1 ? MonsterTips.Mode.Off : MonsterTips.Mode.All;
            if (m_menu != null && m_index >= 0) m_menu.SetItemString(m_index, Label());
        }

        // SendMessage target of the Tooltips item
        void MsgCrawlModTooltips()
        {
            // ALWAYS, then FIRST TIME, then OFF, then ALWAYS again
            var r = MonsterTips.Tooltips;
            MonsterTips.Tooltips = r == MonsterTips.Repeat.Always ? MonsterTips.Repeat.FirstTime
                                 : r == MonsterTips.Repeat.FirstTime ? MonsterTips.Repeat.Off : MonsterTips.Repeat.Always;
            if (m_menu != null && m_indexTooltips >= 0) m_menu.SetItemString(m_indexTooltips, LabelTooltips());
        }
    }
}
