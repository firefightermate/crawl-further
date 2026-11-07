using System;
using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Gods
{
    using CrawlFurther.Util;

    /// <summary>
    /// The evolve screen for players with more than three starters or a slot god (idol).
    ///
    /// Four starters: the player's panel gets a fourth monster button, a copy of the third placed in the button grid
    /// between the third and READY. In the level5 camera (panel origin y 1) the name ends at y 49.4, the "UPGRADE
    /// MONSTER" line spans 45.7 to 32.6 and the WRATH line starts at -52, so 84.6 units are free for four 18-unit buttons
    /// and the 14-unit READY (86 at full size). The button menu is drawn at 15/16 (buttons 16.9 tall, 17.25 apart, READY
    /// 13.1): the first button's top sits at 32 and READY's foot at -50.5. Nothing scrolls, at any player count.
    ///
    /// A slot god: its metal's ribbon tails either side of the player's name (never under it, so the name keeps its
    /// contrast in every player colour) and a bracket either side of every monster button.
    /// </summary>
    public static class EvolveScreen
    {
        static readonly AccessTools.FieldRef<MenuEvolvePlayer, PlayerData> s_pd = AccessTools.FieldRefAccess<MenuEvolvePlayer, PlayerData>("m_playerData");
        static readonly AccessTools.FieldRef<MenuEvolvePlayer, MenuButtonMenu> s_menu = AccessTools.FieldRefAccess<MenuEvolvePlayer, MenuButtonMenu>("m_menu");
        /// <summary>Button-menu indices of READY and of the fourth monster button once it is added.</summary>
        public const int ReadyFour = 13, Button4 = 10;
        /// <summary>The button menu's scale for four starters, and the button / READY centres in the menu's own units
        /// (panel-local centres 22.56 / 5.31 / -11.94 / -29.19 and READY -44.94, divided by the scale).</summary>
        public const float FourScale = 0.9375f;
        public static readonly float[] FourY = { 24.06f, 5.66f, -12.74f, -31.14f };
        public const float ReadyY = -47.94f;

        public static PlayerData Data(MenuEvolvePlayer p) { return s_pd(p); }
        static readonly HashSet<MenuEvolvePlayer> s_logged = new HashSet<MenuEvolvePlayer>();

        /// <summary>True when the panel's player has four (or more) starters.</summary>
        public static bool Four(MenuEvolvePlayer p)
        {
            var pd = s_pd(p);
            return pd != null && pd.GameData != null && pd.GameData.GetMonsterData() != null && pd.GameData.GetMonsterData().Length >= 4;
        }

        /// <summary>The slot tier of the player's god (Normal for an ordinary god).</summary>
        public static SlotTier SlotTierOf(MenuEvolvePlayer p)
        {
            var pd = s_pd(p);
            return pd != null ? SlotGods.Tier(pd.GetDeity()) : SlotTier.Normal;
        }

        /// <summary>Add the fourth monster button (once per evolve panel) once the button menu has its buttons.</summary>
        public static void AddFourth(MenuEvolvePlayer p)
        {
            var menu = s_menu(p);
            var items = R.Get<List<MenuButton>>(menu, "m_items");
            if (items != null && items.Count == 14 && items[10] != null && items[10].name == "ButtonMonster4") return;   // done
            if (items == null || items.Count != 11 || items[7] == null || items[10] == null
                || items[7].GetComponent<MenuButtonEvolveMonster>() == null || items[10].GetComponent<MenuButtonEvolveMonster>() != null)
            {
                FurtherCore.Log.LogWarning("Evolve: no fourth button, unexpected button menu (" + (items == null ? "null" : items.Count + " items") + ")");
                return;
            }
            var b3 = items[7];
            var ready = items[10];
            var go = UnityEngine.Object.Instantiate(b3.gameObject);
            go.name = "ButtonMonster4";
            // Instantiate leaves the copy unparented at b3's world position: parent it and copy b3's local placement,
            // or the world coordinates become local ones and the button lands outside the panel
            go.transform.SetParent(b3.transform.parent, false);
            go.transform.localPosition = b3.transform.localPosition;
            go.transform.localRotation = b3.transform.localRotation;
            go.transform.localScale = b3.transform.localScale;
            BoxView.ResetCopiedClips(go);           // its own clip plane and plain materials, not button 3's clip material
            go.AddComponent<ClipMaterialOwner>();
            var b4 = go.GetComponent<MenuButton>();
            b4.Initialise(R.Get<GameObject>(menu, "m_owner"));
            items.RemoveAt(10);
            items.Add(b4); items.Add(null); items.Add(null); items.Add(ready);
            R.Get<List<MenuButton>>(menu, "m_itemsAll").Add(b4);
            for (int i = 0; i < 4; i++)
            {
                var b = items[1 + i * 3];
                var lp = b.transform.localPosition;
                b.transform.localPosition = new Vector3(lp.x, FourY[i], lp.z);
            }
            var rp = ready.transform.localPosition;
            ready.transform.localPosition = new Vector3(rp.x, ReadyY, rp.z);
            var keep = menu.gameObject.GetComponent<KeepLocalScale>() ?? menu.gameObject.AddComponent<KeepLocalScale>();
            keep.scale = new Vector3(FourScale, FourScale, 1f);
            menu.transform.localScale = keep.scale;
            FurtherCore.Log.LogInfo("Evolve: fourth monster button for player " + (Data(p) != null ? Data(p).Id : -1));
        }

        /// <summary>Brackets on each monster button and the ribbon behind the name, in the slot god's metal.</summary>
        public static void Decorate(MenuEvolvePlayer p)
        {
            var tier = SlotTierOf(p);
            if (tier == SlotTier.Normal) return;
            if (!s_logged.Contains(p))
            {
                s_logged.Add(p);
                var pd = s_pd(p);
                FurtherCore.Log.LogInfo("Evolve: player " + (pd != null ? pd.Id : -1) + " has the " + tier + " slot god, "
                                   + (pd != null && pd.GameData != null ? pd.GameData.GetMonsterData().Length : 0) + " starters");
            }
            string anim = SlotArt.Anim(tier);
            var bracket = Art("EvoBracket", anim);
            var header = Art("EvoHeader", anim);
            var menu = s_menu(p);
            var items = R.Get<List<MenuButton>>(menu, "m_items");
            if (items != null && bracket != null)
                for (int i = 1; i < items.Count; i += 3)
                {
                    var b = items[i];
                    if (b == null || b.GetComponent<MenuButtonEvolveMonster>() == null || b.transform.Find("ModIdolBracketL") != null) continue;
                    var l = SlotArt.Sprite("ModIdolBracketL", b.transform, new Vector3(-22.5f, 0f, -0.5f), bracket);
                    var r = SlotArt.Sprite("ModIdolBracketR", b.transform, new Vector3(22.5f, 0f, -0.5f), bracket);
                    r.scale = new Vector2(-1f, 1f);
                }
            var name = R.Get<OverlayText>(p, "m_name");
            if (name != null && header != null && p.transform.Find("ModIdolHeader") == null)
            {
                var lp = p.transform.InverseTransformPoint(name.transform.position);
                var h = SlotArt.Sprite("ModIdolHeader", p.transform, new Vector3(lp.x, lp.y, lp.z + 0.4f), header);
                h.gameObject.AddComponent<FollowActive>().target = name.gameObject;
            }
        }

        static readonly HashSet<string> s_missing = new HashSet<string>();

        /// <summary>A slot art clip that can be drawn, or null (logged once): the frame is left out rather than drawn blank.</summary>
        static exSpriteAnimClip Art(string sheet, string anim)
        {
            var c = SlotArt.Clip(sheet, anim);
            if (SlotArt.Alive(c)) return c;
            if (s_missing.Add(sheet + "/" + anim)) FurtherCore.Log.LogWarning("Evolve: no " + sheet + " " + anim + " art, the slot god frame is left out");
            return null;
        }
    }

    /// <summary>A slot god's frame on the evolve panel.</summary>
    [HarmonyPatch(typeof(MenuEvolvePlayer), "Initialise")]
    static class Patch_EvolveIdolHeader
    {
        static void Postfix(MenuEvolvePlayer __instance)
        {
            try { EvolveScreen.Decorate(__instance); } catch (Exception e) { FurtherCore.Log.LogWarning("Evolve slot god frame: " + e.Message); }
        }
    }

    /// <summary>The fourth monster button, when the player is already known as the button menu starts.</summary>
    [HarmonyPatch(typeof(MenuEvolvePlayer), "OnMenuInitialised")]
    static class Patch_EvolveFourthButton
    {
        static void Prefix(MenuEvolvePlayer __instance)
        {
            try { if (EvolveScreen.Four(__instance)) EvolveScreen.AddFourth(__instance); }
            catch (Exception e) { FurtherCore.Log.LogError("Evolve fourth monster button: " + e); }
        }
    }

    /// <summary>
    /// The fourth monster button and its monster. OnMenuInitialised usually fires before MenuEvolvePlayer.Initialise has
    /// set the player; InitMonsterButtons runs again on entering the Menu state, after Initialise.
    /// </summary>
    [HarmonyPatch(typeof(MenuEvolvePlayer), "InitMonsterButtons")]
    static class Patch_EvolveFourthInit
    {
        static void Prefix(MenuEvolvePlayer __instance)
        {
            try { if (EvolveScreen.Four(__instance)) EvolveScreen.AddFourth(__instance); }
            catch (Exception e) { FurtherCore.Log.LogError("Evolve fourth monster button: " + e); }
        }

        static void Postfix(MenuEvolvePlayer __instance, MenuButtonMenu ___m_menu)
        {
            try
            {
                if (EvolveScreen.Four(__instance))
                {
                    var b = ___m_menu.GetButton(EvolveScreen.Button4);
                    var m = b != null ? b.GetComponent<MenuButtonEvolveMonster>() : null;
                    if (m != null) m.SetMonsterData(EvolveScreen.Data(__instance), 3);
                }
                EvolveScreen.Decorate(__instance);
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Evolve fourth monster init: " + e.Message); }
        }
    }

    /// <summary>Back in the evolve menu jumps to READY (vanilla hard-codes button 10, which is the fourth monster here).</summary>
    [HarmonyPatch(typeof(MenuEvolvePlayer), "OnUpdateState")]
    static class Patch_EvolveFourthBack
    {
        static System.Reflection.MethodInfo s_desc;
        static bool Prefix(MenuEvolvePlayer __instance, string state, MenuButtonMenu ___m_menu)
        {
            if (state != "Menu") return true;
            try
            {
                if (!EvolveScreen.Four(__instance)) return true;
                var items = R.Get<List<MenuButton>>(___m_menu, "m_items");
                if (items == null || items.Count < 14) return true;
                if (s_desc == null) s_desc = AccessTools.Method(typeof(MenuEvolvePlayer), "UpdateMenuDescriptionText");
                s_desc.Invoke(__instance, null);
                var pd = EvolveScreen.Data(__instance);
                if (pd != null && pd.GetInputDownBack() && pd.ControllerId != eController.Mouse && !___m_menu.GetActioning())
                {
                    if (___m_menu.GetSelectedId() == EvolveScreen.ReadyFour) ___m_menu.ActionSelected();
                    else ___m_menu.SetSelectedItem(EvolveScreen.ReadyFour, animate: true);
                }
                return false;
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Evolve fourth back: " + e.Message); return true; }
        }
    }
}
