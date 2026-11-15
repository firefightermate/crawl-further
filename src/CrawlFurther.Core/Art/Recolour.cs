#if CHAOS_NEXT
// Next chaos update: compiled only with CHAOS_NEXT (build.sh sets it unless NO_CHAOS_NEXT=1).
using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Art
{
    using CrawlFurther.Game;

    /// <summary>
    /// Recolouring the game's own art at runtime, for a biome's rooms, doors and props: each sprite frame used is cut
    /// from its atlas (read on the GPU, so nothing of the game's is shipped), run through a colour function and put
    /// back as a one-frame atlas of ours. Animations get copies of their clips pointing at the recoloured frames.
    /// Results are cached by (atlas, frame, key), so the same frame recoloured the same way is made once.
    /// </summary>
    public static class Recolour
    {
        /// <summary>A colour function; it keeps alpha unless it means to change it.</summary>
        public delegate Color32 Fn(Color32 c);

        static readonly Dictionary<string, exAtlas> s_frames = new Dictionary<string, exAtlas>();
        static readonly Dictionary<string, exSpriteAnimClip> s_clips = new Dictionary<string, exSpriteAnimClip>();

        /// <summary>Shading kept, colour moved: hue turned toward <paramref name="h"/> (0..1) by <paramref name="hmix"/>,
        /// saturation times <paramref name="sk"/> plus <paramref name="sadd"/>, value times <paramref name="vk"/>.</summary>
        public static Fn Hsv(float h, float sk, float vk, float hmix, float sadd = 0f)
        {
            return c =>
            {
                if (c.a == 0) return c;
                float hh, s, v;
                Color.RGBToHSV(c, out hh, out s, out v);
                float d = ((h - hh + 1.5f) % 1f) - 0.5f;
                hh = (hh + d * hmix + 1f) % 1f;
                s = Mathf.Clamp01(s * sk + sadd);
                v = Mathf.Clamp01(v * vk);
                Color32 o = Color.HSVToRGB(hh, s, v);
                o.a = c.a;
                return o;
            };
        }

        /// <summary>The frame <paramref name="index"/> of <paramref name="atlas"/>, recoloured: a one-frame atlas of ours.
        /// Null if the frame can't be read.</summary>
        public static exAtlas Frame(exAtlas atlas, int index, string key, Fn fn)
        {
            if (atlas == null || atlas.texture == null || atlas.elements == null || index < 0 || index >= atlas.elements.Length) return null;
            string k = atlas.GetInstanceID() + ":" + index + ":" + key;
            exAtlas o;
            if (s_frames.TryGetValue(k, out o)) return o;
            o = null;
            try
            {
                var el = atlas.elements[index];
                var t = ChaosRooms.Readable(atlas.texture);
                int x = Mathf.RoundToInt(el.coords.x * t.width), y = Mathf.RoundToInt(el.coords.y * t.height);
                int w = Mathf.Max(1, Mathf.RoundToInt(el.coords.width * t.width)), h = Mathf.Max(1, Mathf.RoundToInt(el.coords.height * t.height));
                var c = t.GetPixels(x, y, w, h);
                var px = new Color32[c.Length];
                for (int i = 0; i < c.Length; i++) px[i] = fn(c[i]);
                var tex = new Texture2D(w, h, TextureFormat.ARGB32, false) { name = "Recolour_" + el.name + "_" + key, filterMode = FilterMode.Point, wrapMode = TextureWrapMode.Clamp };
                tex.SetPixels32(px);
                tex.Apply(false);
                var ne = new exAtlas.Element
                {
                    name = el.name, originalWidth = el.originalWidth, originalHeight = el.originalHeight,
                    trimRect = el.trimRect, coords = new Rect(0f, 0f, 1f, 1f), rotated = el.rotated,
                };
                o = SpriteUtil.MakeAtlas(tex.name, tex, new[] { ne }, atlas.material);
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Recolour: " + atlas.name + " frame " + index + ": " + e.Message); o = null; }
            s_frames[k] = o;
            return o;
        }

        /// <summary>A copy of <paramref name="clip"/> whose frames are recoloured (the clip itself if none could be).</summary>
        public static exSpriteAnimClip Clip(exSpriteAnimClip clip, string key, Fn fn)
        {
            if (clip == null) return null;
            string k = clip.GetInstanceID() + ":" + key;
            exSpriteAnimClip o;
            if (s_clips.TryGetValue(k, out o)) return o;
            o = UnityEngine.Object.Instantiate(clip);
            o.name = clip.name;
            bool any = false;
            foreach (var f in o.frameInfos)
            {
                var a = Frame(f.atlas, f.index, key, fn);
                if (a == null) continue;
                f.atlas = a; f.index = 0; any = true;
            }
            if (!any) { UnityEngine.Object.DestroyImmediate(o); o = clip; }
            else SpriteSheets.Keep(o);
            s_clips[k] = o;
            return o;
        }

        /// <summary>Recolour every sprite and sprite animation under <paramref name="root"/> (inactive ones too) with
        /// <paramref name="pick"/>'s function for it; a null function leaves that sprite alone.</summary>
        public static void Tree(GameObject root, Func<exSprite, KeyValuePair<string, Fn>> pick)
        {
            if (root == null) return;
            foreach (var s in root.GetComponentsInChildren<exSprite>(true))
            {
                var f = pick(s);
                if (f.Value == null) continue;
                var anim = s.GetComponent<exSpriteAnimation>();
                if (anim != null && anim.animations != null)
                {
                    var def = anim.defaultAnimation;
                    for (int i = 0; i < anim.animations.Count; i++)
                    {
                        var c = Clip(anim.animations[i], f.Key, f.Value);
                        if (anim.animations[i] == def) anim.defaultAnimation = c;
                        anim.animations[i] = c;
                    }
                    if (anim.defaultAnimation == def && def != null) anim.defaultAnimation = Clip(def, f.Key, f.Value);
                }
                if (s.atlas == null) continue;
                var a = Frame(s.atlas, s.index, f.Key, f.Value);
                if (a == null) continue;
                s.SetSprite(a, 0);
                var r = s.GetComponent<Renderer>();
                if (r != null && a.material != null) r.sharedMaterial = a.material;
            }
        }

        /// <summary>Recolour everything under <paramref name="root"/> the same way.</summary>
        public static void Tree(GameObject root, string key, Fn fn)
        {
            Tree(root, s => new KeyValuePair<string, Fn>(key, fn));
        }
    }
}
#endif
