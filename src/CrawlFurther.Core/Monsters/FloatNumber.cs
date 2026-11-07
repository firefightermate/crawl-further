using UnityEngine;

namespace CrawlFurther.Monsters
{
    using CrawlFurther.Art;
    using CrawlFurther.Util;

    /// <summary>
    /// Arcade-style floating numbers (dice rolls and the like), drawn from the FxCommonDigits sheet: chunky 5 x 7 digits
    /// in Crawl's bitmap-font style at the size of the game's in-world text, with a 1 px dark outline and drop shadow.
    /// Each number pops white-hot for 0.08 s, springs up 9 px, bounces back 3, then floats up and fades, gone 0.8 s after
    /// it appeared. Numbers sort in front of every character, snap to whole pixels and come from a fixed pool. A number
    /// spawned close to one that is still young is shifted sideways and 4 px up, so dice that land together read apart.
    /// </summary>
    public static class FloatNumber
    {
        /// <summary>The digit sheet (glyphs 0-9 and D O G E, in each <see cref="NumberTone"/>).</summary>
        public const string Sheet = "FxCommonDigits";
        /// <summary>Seconds a number stays on screen.</summary>
        public const float Life = 0.8f;

        /// <summary>A roll of <paramref name="value"/> on a die with <paramref name="max"/> faces, its bottom-centre at
        /// <paramref name="at"/>. <paramref name="like"/> (optional) is a sprite whose render camera the number joins.</summary>
        public static void Roll(int value, int max, Vector2 at, GameObject like = null)
        {
            Show(value.ToString(), ToneFor(value, max), at, like);
        }

        /// <summary>A roll shown over <paramref name="who"/>'s head (<paramref name="lift"/> px above its top).</summary>
        public static void RollOver(GameObject who, int value, int max, float lift = 2f)
        {
            if (who == null) return;
            Roll(value, max, OverHead(who, lift), who);
        }

        /// <summary>Any short run of the sheet's glyphs (0-9, D O G E), e.g. "DODGE".</summary>
        public static void Show(string text, NumberTone tone, Vector2 at, GameObject like = null)
        {
            try { var pool = FloatNumberPool.Get(); if (pool != null) pool.Spawn(text, tone, at, like); }
            catch (System.Exception e) { FloatNumberPool.LogOnce(e); }
        }

        /// <summary>Gold for the top face, grey-red for a 1, cream otherwise.</summary>
        public static NumberTone ToneFor(int value, int max)
        {
            if (value >= max) return NumberTone.Max;
            if (value <= 1) return NumberTone.Min;
            return NumberTone.Normal;
        }

        /// <summary>The point <paramref name="lift"/> px above the top of a body: its hurtbox, checked against the art
        /// (a mod sheet's opaque frame bounds, a vanilla sprite's trimmed quad), as the status overlays measure it.</summary>
        public static Vector2 OverHead(GameObject who, float lift = 2f)
        {
            if (who == null) return Vector2.zero;
            var tr = who.transform;
            float feetY = tr.position.y, top = 16f, cx = tr.position.x;
            var box = ModUtil.Hurtbox(who);
            if (box != null)
            {
                var b = box.bounds;
                top = b.max.y - feetY;
                cx = b.center.x;
            }
            float sTop = -1f;
            var spr = who.GetComponent<exSprite>();
            if (spr != null && spr.enabled && spr.atlas != null)
            {
                var sh = SpriteSheets.ByAtlas(spr.atlas);
                int bx, by, bw, bh;
                if (sh != null)
                {
                    if (MonsterFactory.Bounds(sh, spr.index, out bx, out by, out bw, out bh))
                        sTop = (spr.offset.y + by + bh) * Mathf.Abs(tr.lossyScale.y);
                }
                else
                {
                    var r = who.GetComponent<Renderer>();
                    if (r != null && r.enabled) sTop = r.bounds.max.y - feetY;
                }
            }
            if (sTop > 0f) top = box != null ? Mathf.Max(top, Mathf.Min(sTop, top + 14f)) : sTop;
            return new Vector2(cx, feetY + top + lift);
        }
    }
}
