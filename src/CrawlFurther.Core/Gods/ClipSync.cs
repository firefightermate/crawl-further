using System;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Gods
{
    using CrawlFurther.Compat;

    /// <summary>
    /// Keeps clipped menu sprites on the right texture when they switch between monsters drawn on different sheets.
    ///
    /// ex2D clip planes (exClipping) keep one clip material per texture and remember, per sprite, the material it had
    /// when it was first added. Vanilla monsters all share AtlasEnemies, so a menu sprite never changes texture; mod
    /// monsters each have their own sheet, and two things go wrong in the menus that clip a monster (evolve menu buttons,
    /// level results, the library, the HUD portrait):
    ///  1. exSprite.SetSprite with a new atlas puts the plain atlas material back, and AddPlane returns at once because
    ///     the sprite is already registered, so there is no clip material. The game then switches the material to
    ///     SpriteTintedClipping, whose _ClipRect defaults to zero: nothing is drawn.
    ///  2. exClipping.OnDisable/OnEnable put back the material recorded at the first AddPlane, and SetSprite leaves
    ///     materials alone when the atlas is unchanged: the old monster's texture is drawn under the new one's UVs.
    /// <see cref="Sync"/> puts the clip material for the texture the sprite really shows on its renderer, and records the
    /// plain material so a later disable/enable restores the right one.
    /// </summary>
    public static class ClipSync
    {
        static bool IsMod(Texture t) { return OnlineNames.IsModTexture(t); }

        /// <summary>True if the sprite or its current material involves mod art (vanilla-only sprites are left alone).</summary>
        static bool Involved(exSprite s, Material m)
        {
            return (s.atlas != null && IsMod(s.atlas.texture)) || (m != null && IsMod(m.mainTexture));
        }

        /// <summary>Match the sprite's material to its atlas (and its clip plane, when it has one). Vanilla-only sprites are left alone.</summary>
        public static void Sync(exSprite s)
        {
            if (s == null || s.atlas == null || s.atlas.material == null) return;
            var r = s.GetComponent<Renderer>();
            if (r == null) return;
            var tex = s.atlas.texture as Texture2D;
            var cur = r.sharedMaterial;
            if (tex == null || !Involved(s, cur)) return;
            var clip = s.clippingPlane;
            if (clip == null || !clip.HasPlaneInfo(s))
            {
                // not clipped (yet): just make the material match the atlas, AddPlane will clip the right texture
                if (cur == null || cur.mainTexture != tex) { r.sharedMaterial = s.atlas.material; Retint(s); }
                return;
            }
            if (cur != null && cur.mainTexture == tex)
            {
                if (clip.clipMaterialList.Contains(cur)) return;                        // the plane's own clip material
                if (cur.shader != null && cur.shader.name.Contains("Clipping"))
                {
                    // a clip-shader copy the game made of it (SetPalettedClipShader): keep feeding it the clip rect, and keep
                    // the texture in the table (a dynamic clipper's RemovePlane looks it up)
                    if (!clip.textureToClipMaterialTable.ContainsKey(tex)) clip.AddClipMaterial(tex, cur);
                    else clip.clipMaterialList.Add(cur);
                    return;
                }
            }
            r.sharedMaterial = s.atlas.material;
            clip.UpdatePlane(s);   // records the plain material, then applies (or creates) the clip material for this texture
            Retint(s);
        }

        static void Retint(exSprite s)
        {
            var t = s.GetComponent<ColorTinterBase>();
            if (t != null) t.ReapplyTint();
        }
    }

    /// <summary>Every menu calls AddPlane right after SetupPortrait / SetSprite, before it picks the clip shader.</summary>
    [HarmonyPatch(typeof(exClipping), "AddPlane")]
    static class Patch_ClipAddPlane
    {
        static void Prefix(exPlane _plane)
        {
            try { ClipSync.Sync(_plane as exSprite); } catch (Exception e) { FurtherCore.Log.LogWarning("Clip sync: " + e.Message); }
        }
    }

    [HarmonyPatch(typeof(Player), "SetupPortrait")]
    static class Patch_ClipSetupPortrait
    {
        static void Postfix(exSprite portraitSprite)
        {
            try { ClipSync.Sync(portraitSprite); } catch (Exception e) { FurtherCore.Log.LogWarning("Clip sync: " + e.Message); }
        }
    }

    [HarmonyPatch(typeof(Player), "SetupPortraitAnimRun")]
    static class Patch_ClipSetupPortraitRun
    {
        static void Postfix(exSprite portraitSprite)
        {
            try { ClipSync.Sync(portraitSprite); } catch (Exception e) { FurtherCore.Log.LogWarning("Clip sync: " + e.Message); }
        }
    }

    /// <summary>The level-results monster's tinted copy is clipped to the wrath fill and re-set from the main sprite every
    /// frame; a new monster's atlas knocked its clip material off (the tint covered the whole monster).</summary>
    [HarmonyPatch(typeof(MenuLevelResultsMonster), "Update")]
    static class Patch_ClipLevelResultsMonster
    {
        static void Postfix(exSprite ___m_tintedSprite)
        {
            try { ClipSync.Sync(___m_tintedSprite); } catch { }
        }
    }
}
