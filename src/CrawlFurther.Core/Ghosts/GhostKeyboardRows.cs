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

    /// <summary>The ghost rows of Options > Keyboards (on the MenuKeyboards object).</summary>
    public class GhostKeyboardRows : MonoBehaviour
    {
        public const string Header = "- Ghost Button -";
        MenuKeyboards m_kb;

        public static GhostKeyboardRows Ensure(MenuKeyboards kb)
        {
            var rows = kb.GetComponent<GhostKeyboardRows>() ?? kb.gameObject.AddComponent<GhostKeyboardRows>();
            rows.m_kb = kb;
            var menu = rows.Menu;
            if (menu == null || rows.Base >= 0) return rows;
            if (R.Get<bool>(menu, "m_initialised"))
            {
                FurtherCore.Log.LogWarning("Ghost button: the Keyboards page was already built, no ghost rows");
                return rows;
            }
            menu.m_itemsData.Add(new MenuTextMenuItemData { m_text = Header, m_enabled = false, m_visible = true });
            for (int i = 0; i < 4; i++)
                menu.m_itemsData.Add(new MenuTextMenuItemData { m_text = "Ghost " + (i + 1) + ":", m_enabled = true, m_visible = true, m_message = "MsgGhostKeys" + (i + 1) });
            menu.m_itemsData.Add(new MenuTextMenuItemData { m_text = "Mouse:middle click", m_enabled = false, m_visible = true });
            return rows;
        }

        MenuTextMenu Menu { get { return m_kb != null ? R.Get<MenuTextMenu>(m_kb, "m_menuOptions") : null; } }
        int Base { get { var m = Menu; return m != null ? m.m_itemsData.FindIndex(d => d != null && d.m_text == Header && !d.m_enabled) : -1; } }

        void MsgGhostKeys1() { Listen(0); }
        void MsgGhostKeys2() { Listen(1); }
        void MsgGhostKeys3() { Listen(2); }
        void MsgGhostKeys4() { Listen(3); }

        void Listen(int i)
        {
            var st = R.Get<MenuStateMachine>(m_kb, "m_state");
            var l = GhostBindListener.For(R.Get<MenuInputBinding>(m_kb, "m_menuInputBind"));
            if (st == null || l == null) return;
            int cid = (int)eController.Keyboard1 + i;
            GhostControls.ClearMoved(cid);
            l.Begin(cid, "keys " + (i + 1), true, ok =>
            {
                st.QueueState("Options");
                Refresh();
            });
            st.QueueState("Bind");
        }

        public void Refresh()
        {
            var menu = Menu;
            int b = Base;
            if (menu == null || b < 0) return;
            for (int i = 0; i < 4; i++)
            {
                int cid = (int)eController.Keyboard1 + i;
                menu.SetItemString(b + 1 + i, "Ghost " + (i + 1) + (GhostControls.Moved(cid) ? " now:" : ":") + GhostControls.NameOf(cid));
            }
            menu.SetItemString(b + 5, "Mouse:" + GhostControls.NameOf((int)eController.Mouse));
        }

        void OnDisable()
        {
            for (int c = (int)eController.Keyboard1; c <= (int)eController.Keyboard4; c++) GhostControls.ClearMoved(c);
        }
    }

    [HarmonyPatch(typeof(MenuKeyboards), "OnEnable")]
    static class Patch_GhostKeyboardRowsAdd
    {
        static void Prefix(MenuKeyboards __instance)
        {
            try { GhostKeyboardRows.Ensure(__instance); }
            catch (Exception e) { FurtherCore.Log.LogWarning("Ghost button rows (keyboards): " + e.Message); }
        }
    }

    [HarmonyPatch(typeof(MenuKeyboards), "InitMenuText")]
    static class Patch_GhostKeyboardRowsText
    {
        static void Postfix(MenuKeyboards __instance)
        {
            try { GhostControls.Changed(); var rows = __instance.GetComponent<GhostKeyboardRows>(); if (rows != null) rows.Refresh(); }
            catch (Exception e) { FurtherCore.Log.LogWarning("Ghost button rows text (keyboards): " + e.Message); }
        }
    }

    /// <summary>"Reset All" resets the four keyboards' ghost keys too (InitMenuText then shows them).</summary>
    [HarmonyPatch(typeof(MenuKeyboards), "MsgReset")]
    static class Patch_GhostKeyboardsReset
    {
        static void Prefix() { try { GhostControls.Watch(); GhostControls.ResetKeyboards(); } catch (Exception e) { FurtherCore.Log.LogWarning("Ghost button reset (keyboards): " + e.Message); } }
    }

    /// <summary>"Reset Keys N" (a bound keyboard's row) resets that keyboard's ghost key too; "Bind Keys N" snapshots the
    /// ghost keys first, so a key the new binding takes shows as moved.</summary>
    [HarmonyPatch(typeof(MenuKeyboards), "OnKeysSelected")]
    static class Patch_GhostKeyboardsKeys
    {
        static void Prefix(int i)
        {
            try
            {
                var cid = (eController)((int)eController.Keyboard1 + i);
                GhostControls.Watch();
                if (Singleton<SystemInput>.Get.GetControllerHasBinding(cid)) GhostControls.Reset((int)cid);
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Ghost button keys (keyboards): " + e.Message); }
        }
    }

    // ------------------------------------------------------------------ Options > Reset Controls (every controller)
    [HarmonyPatch(typeof(MenuOptions), "MsgResetControls")]
    static class Patch_GhostResetAll
    {
        static void Postfix() { try { GhostControls.ResetAll(); GhostControls.Changed(); } catch (Exception e) { FurtherCore.Log.LogWarning("Ghost button reset (options): " + e.Message); } }
    }
}
