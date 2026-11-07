using System;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Gods
{
    using CrawlFurther.Art;
    using CrawlFurther.Monsters;
    using CrawlFurther.UI;

    /// <summary>
    /// Fits wide evolution choices into the evolve menu's two hands. In the level5 scene the hands sit at x -16 / +16.9
    /// inside a 55 px wide player panel, the monster stands at y -4.5 in the hand, the cost numbers sit at y 44 and a
    /// selected hand rises to y 12. Vanilla monsters are about 20 px wide; a 42 px mod monster would overlap the other
    /// hand, the next player's panel and the cost number.
    ///
    /// Each choice is shifted outward (whole pixels) as far as the panel allows and drawn at the largest scale in
    /// [0.6, 1] (multiples of 1/16: the menu camera draws about 7.7 px per unit, so these stay crisp) that keeps it 1.5 px
    /// clear of the centre line and its top 2 px under the cost number (dropping up to 6 px into the fist). It is never
    /// drawn shorter than the current monster below it: when that scale does not fit, it crosses the centre line instead
    /// (4 px, more only when its height needs it) and the selected hand is drawn in front. Units are pixels.
    /// </summary>
    public static class EvolveHands
    {
        public const float Centre = 0.45f, PanelHalf = 27.5f, Edge = 0.5f, Gap = 1.5f, TopLimit = 30f, MaxDrop = 6f,
                           Cross = 4f, KMin = 0.6f, MonsterZ = -30f;
        public const int Step = 16;

        /// <summary>Opaque height of what a prefab sprite shows (mod sheet bounds; vanilla frames are trimmed).</summary>
        public static float ArtHeight(exSprite s)
        {
            if (s == null || s.atlas == null) return 0f;
            var sh = SpriteSheets.ByAtlas(s.atlas);
            int bx, by, bw, bh;
            if (sh != null) return MonsterFactory.Bounds(sh, s.index, out bx, out by, out bw, out bh) ? bh : 0f;
            if (s.atlas.elements == null || s.index < 0 || s.index >= s.atlas.elements.Length) return 0f;
            return s.atlas.elements[s.index].trimRect.height;
        }

        /// <summary>Scale and offset an evolution choice's sprite in its hand (vanilla art is put back to scale 1).</summary>
        public static void Place(exSprite s, float currentHeight)
        {
            if (s == null || s.transform.parent == null) return;
            var sh = SpriteSheets.ByAtlas(s.atlas);
            int bx, by, bw, bh;
            if (sh == null || !MonsterFactory.Bounds(sh, s.index, out bx, out by, out bw, out bh))
            {
                s.scale = Vector2.one;   // vanilla monster in a hand that showed a scaled mod one before
                return;
            }
            float hx = s.transform.parent.localPosition.x + s.transform.localPosition.x;
            Vector2 off; float k, over;
            Fit(sh.manifest.cellW, bx, by, bw, bh, hx, currentHeight, out k, out off, out over);
            s.scale = new Vector2(k, k);
            s.offset = off;
        }

        static bool TryFit(int cellW, int bx, int by, int bw, int bh, float hx, float k, float cross, out Vector2 off, out float over)
        {
            bool left = hx < Centre;
            float feet = cellW / 2 + 0.5f;     // feet column centre, from the cell's left edge
            float l = (bx - feet) * k, r = (bx + bw - feet) * k, top = (by + bh - 1) * k;
            float lo = -PanelHalf + Edge - hx, hi = PanelHalf - Edge - hx;
            if (left) hi = Mathf.Min(hi, Centre - Gap - hx); else lo = Mathf.Max(lo, Centre + Gap - hx);
            float shift = 0f; bool ok;
            // outward as far as the panel allows; only what is left over may cross the centre line
            if (left)
            {
                if (r > hi) shift = Mathf.Floor(hi - r);
                if (l + shift < lo) shift = Mathf.Ceil(lo - l);
                over = Mathf.Max(0f, r + shift - hi);
                ok = l + shift >= lo - 0.001f && over <= cross + 0.001f;
            }
            else
            {
                if (l < lo) shift = Mathf.Ceil(lo - l);
                if (r + shift > hi) shift = Mathf.Floor(hi - r);
                over = Mathf.Max(0f, lo - (l + shift));
                ok = r + shift <= hi + 0.001f && over <= cross + 0.001f;
            }
            float drop = Mathf.Max(0f, Mathf.Ceil(top - TopLimit));
            ok = ok && drop <= MaxDrop;
            off = new Vector2(shift - (feet - cellW * 0.5f) * k, -k - drop);   // feet column on x = shift, feet row's bottom on -drop
            return ok;
        }

        /// <summary>Scale, sprite offset and centre-line crossing for art bounds (from the cell's bottom-left) in the hand at
        /// x hx, under a current monster currentHeight px tall. False when nothing fits within the limits above.</summary>
        public static bool Fit(int cellW, int bx, int by, int bw, int bh, float hx, float currentHeight, out float k, out Vector2 off, out float over)
        {
            float kHeight = currentHeight >= bh ? 1f : Mathf.Ceil(currentHeight / bh * Step) / Step;   // never shorter than the parent
            float kFloor = Mathf.Max(Mathf.Ceil(KMin * Step) / Step, kHeight);
            float[] crosses = { 0f, Cross, 2f * PanelHalf, 0f, Cross };
            float[] floors = { kFloor, kFloor, kFloor, KMin, KMin };
            for (int pass = 0; pass < crosses.Length; pass++)
            {
                // beyond the 4 px allowance only the smallest scale that keeps the parent's height (least crossing)
                for (int n = Step; n / (float)Step >= floors[pass] - 0.0001f; n--)
                {
                    k = crosses[pass] > Cross ? floors[pass] : n / (float)Step;
                    if (TryFit(cellW, bx, by, bw, bh, hx, k, crosses[pass], out off, out over)) return true;
                    if (crosses[pass] > Cross) break;
                }
            }
            int last = Mathf.CeilToInt(KMin * Step);
            k = last / (float)Step;
            TryFit(cellW, bx, by, bw, bh, hx, k, 2f * PanelHalf, out off, out over);
            return false;
        }
    }

    /// <summary>When a choice is wide enough to cross the centre line, the selected hand's monster is drawn in front.</summary>
    [HarmonyPatch(typeof(MenuEvolvePlayerEvolve), "Update")]
    static class Patch_EvolveHandOrder
    {
        static System.Reflection.FieldInfo s_left, s_right, s_monster;
        static bool s_warned;

        static void Postfix(MenuEvolvePlayerEvolve __instance, int ___m_selectedItem)
        {
            try
            {
                if (s_left == null)
                {
                    s_left = AccessTools.Field(typeof(MenuEvolvePlayerEvolve), "m_handLeft");
                    s_right = AccessTools.Field(typeof(MenuEvolvePlayerEvolve), "m_handRight");
                    s_monster = AccessTools.Field(s_left.FieldType, "m_monster");
                }
                Order(s_monster.GetValue(s_left.GetValue(__instance)) as exSprite, ___m_selectedItem == 0);
                Order(s_monster.GetValue(s_right.GetValue(__instance)) as exSprite, ___m_selectedItem == 1);
            }
            catch (Exception e)
            {
                if (!s_warned) { s_warned = true; FurtherCore.Log.LogWarning("Evolve hand order: " + e.Message); }
            }
        }
        static void Order(exSprite s, bool front)
        {
            if (s == null) return;
            var t = s.transform; var p = t.localPosition;
            float z = front ? EvolveHands.MonsterZ - 0.5f : EvolveHands.MonsterZ;   // the fingers (z -31) stay in front of both
            if (Mathf.Abs(p.z - z) > 0.001f) t.localPosition = new Vector3(p.x, p.y, z);
        }
    }

    /// <summary>Lays out each evolution choice as it is shown and gives it the mod gem.</summary>
    [HarmonyPatch(typeof(MenuEvolvePlayerEvolve), "SetMonsterSprite")]
    static class Patch_EvolveHandBadge
    {
        static void Postfix(MenuEvolvePlayerEvolve __instance, exSprite menuSprite, exSpriteAnimation menuAnim, PlayerMonsterData ___m_monsterDataCurr)
        {
            try
            {
                if (menuAnim == null)
                {
                    var cur = ___m_monsterDataCurr != null && ___m_monsterDataCurr.GetPrefab() != null ? ___m_monsterDataCurr.GetPrefab().GetComponent<exSprite>() : null;
                    EvolveHands.Place(menuSprite, EvolveHands.ArtHeight(cur));
                }
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Evolve hand layout: " + e.Message); }
            try { ModMark.Follow(menuSprite); } catch { }
        }
    }
}
