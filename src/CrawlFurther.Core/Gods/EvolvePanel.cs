using System;
using System.Reflection;
using HarmonyLib;
using UnityEngine;
using CrawlFurther.UI;

namespace CrawlFurther.Gods
{
    using CrawlFurther.UI;

    /// <summary>
    /// The evolve panel (MenuEvolvePlayerEvolve: the monster being evolved, its two choices in the hands, the costs and
    /// the wrath): its one mod gem and the fonts of the numbers vanilla writes into it at run time.
    ///
    /// The gem: one per panel. It marks the monster being evolved when that is mod art, otherwise the selected choice
    /// when that is; the other choice never carries one. Every sprite the panel draws still goes through
    /// <see cref="ModMark.Follow(exSprite, GemCorner, Func{bool})"/> (which keeps one gem per sprite, however often the
    /// panel is shown), so the rule lives in the show conditions below.
    ///
    /// The numbers: in the level5 scene each cost number uses the WRATH label's font and material (CrawlTextBodyWide)
    /// and the wrath number uses BACK's (CrawlMedium). A translation mod that swaps the game's fonts handles the labels,
    /// but a number vanilla sets later can be left with a font and a material that do not belong together, and then its
    /// glyph quads draw as solid boxes. Each number is matched to its label as the panel is drawn: in the vanilla game
    /// they are already the same, so nothing changes there.
    /// </summary>
    public static class EvolvePanel
    {
        static FieldInfo s_left, s_right, s_monster, s_cost;
        static readonly AccessTools.FieldRef<MenuEvolvePlayerEvolve, exSprite> s_curr =
            AccessTools.FieldRefAccess<MenuEvolvePlayerEvolve, exSprite>("m_monsterCurr");
        static readonly AccessTools.FieldRef<MenuEvolvePlayerEvolve, int> s_selected =
            AccessTools.FieldRefAccess<MenuEvolvePlayerEvolve, int>("m_selectedItem");
        static readonly AccessTools.FieldRef<MenuEvolvePlayerEvolve, GameObject> s_wrathBox =
            AccessTools.FieldRefAccess<MenuEvolvePlayerEvolve, GameObject>("m_containerWrath");
        static readonly AccessTools.FieldRef<MenuEvolvePlayerEvolve, TextMesh> s_wrathNum =
            AccessTools.FieldRefAccess<MenuEvolvePlayerEvolve, TextMesh>("m_textWrath");
        static readonly AccessTools.FieldRef<MenuEvolvePlayerEvolve, GameObject> s_back =
            AccessTools.FieldRefAccess<MenuEvolvePlayerEvolve, GameObject>("m_textBack");
        static bool s_loggedFonts;

        static void Init()
        {
            if (s_left != null) return;
            s_left = AccessTools.Field(typeof(MenuEvolvePlayerEvolve), "m_handLeft");
            s_right = AccessTools.Field(typeof(MenuEvolvePlayerEvolve), "m_handRight");
            s_monster = AccessTools.Field(s_left.FieldType, "m_monster");
            s_cost = AccessTools.Field(s_left.FieldType, "m_textCost");
        }

        static object Hand(MenuEvolvePlayerEvolve e, int i) { Init(); return (i == 0 ? s_left : s_right).GetValue(e); }

        /// <summary>The choice sprite in hand <paramref name="i"/> (0 left, 1 right).</summary>
        public static exSprite Choice(MenuEvolvePlayerEvolve e, int i) { var h = Hand(e, i); return h != null ? s_monster.GetValue(h) as exSprite : null; }

        static TextMesh Cost(MenuEvolvePlayerEvolve e, int i) { var h = Hand(e, i); return h != null ? s_cost.GetValue(h) as TextMesh : null; }

        static bool Shown(exSprite s)
        {
            if (s == null || !s.gameObject.activeInHierarchy) return false;
            var r = s.GetComponent<Renderer>();
            return r != null && r.enabled && ModGem.IsModArt(s.atlas);
        }

        /// <summary>Give <paramref name="sprite"/> (the current monster or a choice, as the panel draws it) its share of
        /// the panel's one gem.</summary>
        public static void Gem(MenuEvolvePlayerEvolve e, exSprite sprite)
        {
            if (e == null || sprite == null) return;
            var curr = s_curr(e);
            Func<bool> show = null;
            if (sprite == curr) show = () => Shown(curr);
            for (int i = 0; show == null && i < 2; i++)
            {
                if (Choice(e, i) != sprite) continue;
                int hand = i;
                show = () => e != null && !Shown(s_curr(e)) && s_selected(e) == hand && Shown(sprite);
            }
            if (show != null) ModMark.Follow(sprite, GemCorner.Art, show);
        }

        /// <summary>Match the panel's numbers to their labels' font and material (see the class summary).</summary>
        public static void SyncFonts(MenuEvolvePlayerEvolve e)
        {
            if (e == null) return;
            var box = s_wrathBox(e);
            var label = box != null ? box.transform.Find("Text") : null;
            var wrathLabel = label != null ? label.GetComponent<TextMesh>() : null;
            var back = s_back(e);
            var backText = back != null ? back.GetComponent<TextMesh>() : null;
            bool changed = Match(Cost(e, 0), wrathLabel) | Match(Cost(e, 1), wrathLabel) | Match(s_wrathNum(e), backText);
            if (changed && !s_loggedFonts)
            {
                s_loggedFonts = true;
                FurtherCore.Log.LogInfo("Evolve: the cost and wrath numbers now use their labels' fonts ("
                                        + (wrathLabel.font != null ? wrathLabel.font.name : "?") + ", "
                                        + (backText != null && backText.font != null ? backText.font.name : "?") + "): another mod changed the menu fonts");
            }
        }

        /// <summary>Give <paramref name="t"/> the font, size and material of <paramref name="like"/>; true if anything changed.</summary>
        static bool Match(TextMesh t, TextMesh like)
        {
            if (t == null || like == null || t == like || like.font == null) return false;
            var tr = t.GetComponent<Renderer>();
            var lr = like.GetComponent<Renderer>();
            if (tr == null || lr == null || lr.sharedMaterial == null) return false;
            if (t.font == like.font && tr.sharedMaterial == lr.sharedMaterial && t.fontSize == like.fontSize
                && Mathf.Approximately(t.characterSize, like.characterSize) && t.fontStyle == like.fontStyle) return false;
            t.font = like.font;
            t.fontSize = like.fontSize;
            t.characterSize = like.characterSize;
            t.fontStyle = like.fontStyle;
            tr.sharedMaterial = lr.sharedMaterial;
            return true;
        }
    }

    /// <summary>The panel's numbers get their labels' fonts as it opens (the wrath number shows before any monster).</summary>
    [HarmonyPatch(typeof(MenuEvolvePlayerEvolve), "OnShow")]
    static class Patch_EvolvePanelFonts
    {
        static bool s_warned;
        static void Postfix(MenuEvolvePlayerEvolve __instance)
        {
            try { EvolvePanel.SyncFonts(__instance); }
            catch (Exception e) { if (!s_warned) { s_warned = true; FurtherCore.Log.LogWarning("Evolve panel fonts: " + e.Message); } }
        }
    }
}
