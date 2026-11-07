using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Diagnostics
{
    using CrawlFurther.Art;

    /// <summary>
    /// The F9 developer check of the runtime sprite pipeline: copies the hero and monster atlas textures through the GPU,
    /// swaps their red and blue, builds new atlases on them and repoints every loaded clip frame (and back on the next press).
    /// </summary>
    static class TintTest
    {
        static bool s_on;
        static readonly Dictionary<exAtlas, exAtlas> s_swap = new Dictionary<exAtlas, exAtlas>();

        public static void Toggle()
        {
            try
            {
                s_on = !s_on;
                if (s_on && s_swap.Count == 0) Build();
                int changed = 0;
                foreach (var clip in Resources.FindObjectsOfTypeAll<exSpriteAnimClip>())
                {
                    foreach (var f in clip.frameInfos)
                    {
                        if (f.atlas == null) continue;
                        exAtlas to = null;
                        if (s_on) s_swap.TryGetValue(f.atlas, out to);
                        else foreach (var kv in s_swap) if (kv.Value == f.atlas) to = kv.Key;
                        if (to != null) { f.atlas = to; changed++; }
                    }
                }
                FurtherCore.Log.LogInfo("Tint test " + (s_on ? "ON" : "OFF") + ", frames repointed: " + changed);
            }
            catch (Exception e) { FurtherCore.Log.LogError(e); }
        }

        static void Build()
        {
            foreach (var a in Resources.FindObjectsOfTypeAll<exAtlas>())
            {
                if (a.name != "AtlasEnemies" && a.name != "AtlasHero") continue;
                var copy = SpriteUtil.CopyTexture(a.texture);
                var px = copy.GetPixels32();
                for (int i = 0; i < px.Length; i++)
                {
                    var c = px[i];
                    if (c.a != 0) px[i] = new Color32(c.b, c.g, c.r, c.a);
                }
                copy.SetPixels32(px);
                copy.Apply(false);
                s_swap[a] = SpriteUtil.MakeAtlas(a.name + "_ModTint", copy, a.elements, a.material);
                FurtherCore.Log.LogInfo("Built tinted atlas for " + a.name);
            }
        }
    }
}
