using UnityEngine;

namespace CrawlFurther.Gods
{
    using CrawlFurther.Art;
    using CrawlFurther.Util;

    /// <summary>The violet pip that marks mod entries in the pick lists (gods, hero origins, ghost forms).</summary>
    public static class ModIcons
    {
        static exSpriteAnimClip s_violetPip;

        /// <summary>Size in pixels of the god list's own pip, so other icons can line up with it.</summary>
        public static void GodIconSize(MenuDeitySelectPlayer panel, out int w, out int h)
        {
            w = 16; h = 16;
            try
            {
                var clip = R.Get<exSpriteAnimClip>(panel, "m_deityPortraitDefault");
                if (clip == null || clip.frameInfos.Count == 0) return;
                var f = clip.frameInfos[0];
                var e = f.atlas.elements[f.index];
                if (e.originalWidth > 2 && e.originalHeight > 2) { w = e.originalWidth; h = e.originalHeight; }
            }
            catch { }
        }

        /// <summary>
        /// The pip for a mod entry: a faceted violet gem the size of the vanilla pip (a plain 3 x 4 block). The menu tints
        /// and scales it on selection like the vanilla one. Falls back to the vanilla pip when the art is missing.
        /// </summary>
        public static exSpriteAnimClip VioletPip(MenuDeitySelectPlayer panel)
        {
            if (s_violetPip != null) return s_violetPip;
            var pip = SpriteSheets.Get("ModVioletPip");
            if (pip == null || !pip.Has("Idle")) return VanillaPip(panel);
            s_violetPip = new ClipBuilder(pip, "Idle", "ModVioletPip").Loop().Build();
            return s_violetPip;
        }

        /// <summary>The vanilla pip, for vanilla entries in a list that also holds mod ones.</summary>
        public static exSpriteAnimClip VanillaPip(MenuDeitySelectPlayer panel) { return R.Get<exSpriteAnimClip>(panel, "m_deityPortraitDefault"); }
    }
}
