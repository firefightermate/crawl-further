using System;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Game
{
    using CrawlFurther.Util;

    /// <summary>
    /// The two spells on the player's HUD (GUIPlayer): the game's special bar shows the first spell's charge (also while
    /// the second is being cast through the game's slot), and a copy of it just under, in the ghost button's blue, shows
    /// the second's. The hero stats panel (GUIHeroStats) names both spells.
    /// </summary>
    static class ChaosSpellHud
    {
        const string BarName = "ModChaosSpell2Bar";
        static readonly Color Blue = new Color(86f / 255f, 138f / 255f, 204f / 255f, 1f);

        internal static void AfterUpdate(GUIPlayer gui)
        {
            var bar1 = R.Get<GUIBar>(gui, "m_barSpecial");
            if (bar1 == null) return;
            var t = bar1.transform.parent != null ? bar1.transform.parent.Find(BarName) : null;
            var bar2 = t != null ? t.GetComponent<GUIBar>() : null;
            PlayerData pd = null;
            try { pd = SystemPlayers.GetPlayer(R.Get<int>(gui, "m_playerId")); } catch { }
            bool show = pd != null && ChaosSpells.Active && pd.IsHero && pd.IsAlive && bar1.gameObject.activeSelf
                        && ChaosSpells.Second(pd) != null;
            if (!show)
            {
                if (bar2 != null && bar2.gameObject.activeSelf) bar2.gameObject.SetActive(false);
                return;
            }
            if (bar2 == null) bar2 = Make(bar1);
            if (bar2 == null) return;
            if (!bar2.gameObject.activeSelf) bar2.gameObject.SetActive(true);
            bar1.SetValue(ChaosSpells.Ratio(pd, false));
            bar2.SetValue(ChaosSpells.Ratio(pd, true));
            var p = bar1.transform.localPosition;
            bar2.transform.localPosition = new Vector3(p.x, p.y - Height(bar1), p.z);
        }

        static GUIBar Make(GUIBar bar1)
        {
            var go = (GameObject)UnityEngine.Object.Instantiate(bar1.gameObject);
            go.name = BarName;
            go.transform.SetParent(bar1.transform.parent, false);
            go.transform.localScale = bar1.transform.localScale;
            go.transform.localRotation = bar1.transform.localRotation;
            var bar = go.GetComponent<GUIBar>();
            if (bar == null) { UnityEngine.Object.Destroy(go); return null; }
            bar.SetFrontColor(Blue);
            FurtherCore.Log.LogInfo("Chaos: second spell bar added to " + bar1.transform.root.name);
            return bar;
        }

        /// <summary>The bar's height in its parent's units, plus a one-unit gap.</summary>
        static float Height(GUIBar bar)
        {
            float h = 0f;
            foreach (var r in bar.GetComponentsInChildren<Renderer>(true))
                if (r.enabled) h = Mathf.Max(h, r.bounds.size.y);
            var parent = bar.transform.parent;
            float sy = parent != null ? Mathf.Abs(parent.lossyScale.y) : 1f;
            if (sy < 0.0001f) sy = 1f;
            h = h > 0f ? h / sy : 3f;
            return Mathf.Clamp(h, 1f, 12f) + 1f;
        }

        internal static void AfterStatsText(GUIHeroStats stats)
        {
            if (!ChaosSpells.Active) return;
            var pgd = R.Get<PlayerGameData>(stats, "m_player");
            if (pgd == null) return;
            PlayerData pd = null;
            try { pd = SystemPlayers.GetPlayer(R.Get<int>(pgd, "m_ownerPlayerId")); } catch { }
            var second = pd != null ? ChaosSpells.Second(pd) : null;
            var spell = R.Get<TextMesh>(stats, "m_spell");
            if (second == null || spell == null) return;
            spell.text = ChaosSpells.Name(ChaosSpells.First(pd)) + ", " + ChaosSpells.Name(second);
        }
    }

    /// <summary>The shop's text for a spell says "Replaces" the spell held. In a chaos game it says where the new spell
    /// goes instead: the empty second slot, or one of the two held (the buyer picks).</summary>
    [HarmonyPatch(typeof(GUIGame), "ShowStore")]
    static class Patch_ChaosSpellShopText
    {
        const string Replaces = "\n\nReplaces ";

        static void Prefix(ref string description)
        {
            try
            {
                if (description == null || !ChaosSpells.Active || description.IndexOf(Replaces, StringComparison.Ordinal) < 0) return;
                var hero = SystemLevel.GetHeroPlayerData();
                if (hero == null) return;
                int at = description.IndexOf(Replaces, StringComparison.Ordinal);
                var first = ChaosSpells.First(hero);
                var second = ChaosSpells.Second(hero);
                if (first == null || !ChaosSpells.IsSpell(first)) return;
                string tail = second == null
                    ? "\n\nA second spell, cast with the ghost button (" + Ghosts.GhostControls.Name(hero) + ")"
                    : "\n\nReplaces " + ChaosSpells.Name(first) + " or " + ChaosSpells.Name(second) + " (you pick)";
                var held = hero.GameData.GetPowerupSwappable();
                string vanilla = Replaces + (held != null ? held.GetDisplayName() : "");
                int end = description.StartsWith(vanilla, at) ? at + vanilla.Length : description.Length;
                description = description.Substring(0, at) + tail + description.Substring(end);
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Chaos spell shop text: " + e.Message); }
        }
    }

    static class StringAt
    {
        internal static bool StartsWith(this string s, string part, int at)
        {
            return at >= 0 && at + part.Length <= s.Length && string.CompareOrdinal(s, at, part, 0, part.Length) == 0;
        }
    }

    [HarmonyPatch(typeof(GUIPlayer), "Update")]
    static class Patch_ChaosSpellHud
    {
        static void Postfix(GUIPlayer __instance)
        {
            try { ChaosSpellHud.AfterUpdate(__instance); }
            catch (Exception e) { FurtherCore.Log.LogWarning("Chaos spell bar: " + e.Message); }
        }
    }

    [HarmonyPatch(typeof(GUIHeroStats), "UpdateText")]
    static class Patch_ChaosSpellStats
    {
        static void Postfix(GUIHeroStats __instance)
        {
            try { ChaosSpellHud.AfterStatsText(__instance); }
            catch (Exception e) { FurtherCore.Log.LogWarning("Chaos spell names: " + e.Message); }
        }
    }
}
