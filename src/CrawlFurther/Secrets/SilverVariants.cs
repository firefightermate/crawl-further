using System;
using System.Collections.Generic;
using System.IO;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Content.Secrets
{
    using CrawlFurther.Art;
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// SILVER VARIANTS: the silver ghost's Ascension (GhostSlots / SilverAscended) dresses a tier-3 body in its own
    /// moonlit silver art instead of a colour tint. tools/sprites/silver_variants.py re-renders every frame of every
    /// tier-3 final's sheet (9 gods x 12, the 4 gold-secret finals, the 5 secret statue monsters) into
    /// art/out_silvervar/SilverVar_&lt;sheet&gt;.png (same grid and anims), and every body frame of the 33 vanilla level-3/4
    /// monsters into SilverVar_AtlasEnemies.png (BossFactory's element format: the runtime builds an atlas parallel to the
    /// vanilla AtlasEnemies whose re-rendered elements point into that png).
    ///
    /// How a body wears it: Apply(body) registers the body's exSprites; a prefix on exSprite.SetSprite turns every frame
    /// the animation sets from an original atlas into the same index of its silver atlas (frames, timing, events, hit
    /// geometry and AnimNodes, which read the clip's own atlas, are untouched). Restore(body) (SilverAscended.OnDisable,
    /// i.e. pool reuse) puts the original atlas and material back. A body with no silver art (a silver unique, a monster
    /// outside the lists) returns false and the caller keeps the old tint. Every texture is loaded from the art folder
    /// with a fixed name ("Mod_SilverVar_..."), so Online Crawl clients resolve it locally (nothing is repainted here).
    /// </summary>
    public static class SilverVariants
    {
        public const string Prefix = "SilverVar_";
        public const string VanillaSheet = "SilverVar_AtlasEnemies";

        internal class Map
        {
            public exAtlas silver;
            public bool[] has;          // null: every index (a mod sheet re-rendered cell for cell)
            public HashSet<string> bodies;  // vanilla: the prefabs whose clips were baked (their default sprite may not be)
            public bool Has(int i) { return has == null ? (silver != null && i >= 0 && i < silver.elements.Length) : (i >= 0 && i < has.Length && has[i]); }
        }

        class Worn
        {
            public exSprite spr;
            public Renderer r;
            public Material home;       // the renderer's material before (a vanilla palette material or a tint instance)
            public exAtlas homeAtlas;
        }

        static readonly Dictionary<exAtlas, Map> s_maps = new Dictionary<exAtlas, Map>();
        static readonly HashSet<exAtlas> s_none = new HashSet<exAtlas>();
        static readonly HashSet<exAtlas> s_silver = new HashSet<exAtlas>();
        static readonly Dictionary<GameObject, List<Worn>> s_bodies = new Dictionary<GameObject, List<Worn>>();
        /// <summary>Sprites currently wearing silver (the SetSprite prefix only looks at these).</summary>
        internal static readonly HashSet<exSprite> On = new HashSet<exSprite>();

        /// <summary>Dress <paramref name="body"/> in silver art. False when its main sprite has none (keep the tint).</summary>
        public static bool Apply(GameObject body)
        {
            if (body == null) return false;
            try
            {
                Restore(body);
                Purge();
                var root = body.GetComponent<exSprite>();
                var list = new List<Worn>();
                bool main = false;
                foreach (var spr in body.GetComponentsInChildren<exSprite>(true))
                {
                    if (spr == null || spr.atlas == null) continue;
                    var m = MapFor(spr.atlas);
                    if (m == null) continue;
                    var r = spr.GetComponent<Renderer>();
                    list.Add(new Worn { spr = spr, r = r, home = r != null ? r.sharedMaterial : null, homeAtlas = spr.atlas });
                    On.Add(spr);
                    int idx = spr.index;
                    if (m.Has(idx)) spr.SetSprite(m.silver, idx);
                    if (spr == root && (m.Has(idx) || (m.bodies != null && m.bodies.Contains(BodyName(body))))) main = true;   // an unbaked vanilla body keeps the tint
                }
                if (!main)
                {
                    // no silver art for the body itself: leave everything as it was
                    foreach (var w in list) Put(w);
                    return false;
                }
                s_bodies[body] = list;
                Retint(body);
                return true;
            }
            catch (Exception e) { Plugin.Log.LogError("Silver variant apply failed on " + body.name + ": " + e); return false; }
        }

        /// <summary>Back to the original art (pool reuse, or a body that stops being ascended).</summary>
        public static void Restore(GameObject body)
        {
            if (body == null) return;
            List<Worn> list;
            if (!s_bodies.TryGetValue(body, out list)) return;
            s_bodies.Remove(body);
            try
            {
                foreach (var w in list) Put(w);
                Retint(body);
            }
            catch (Exception e) { Plugin.Log.LogError("Silver variant restore failed on " + body.name + ": " + e); }
        }

        public static bool Wearing(GameObject body) { return body != null && s_bodies.ContainsKey(body); }

        static void Put(Worn w)
        {
            On.Remove(w.spr);                 // first: a sprite destroyed at scene unload must not stay registered
            if (w.spr == null) return;
            var cur = w.spr.atlas;
            if (cur != null && s_silver.Contains(cur))
            {
                // the silver atlas -> the original it shadows (same index)
                exAtlas back = w.homeAtlas;
                foreach (var kv in s_maps) if (kv.Value.silver == cur) { back = kv.Key; break; }
                if (back != null && w.spr.index >= 0 && w.spr.index < back.elements.Length) w.spr.SetSprite(back, w.spr.index);
            }
            // a vanilla monster may draw with its own material (palette swap, tint instance) on the atlas texture
            if (w.r != null && w.home != null && w.spr.atlas != null && w.home.mainTexture == w.spr.atlas.texture)
                w.r.sharedMaterial = w.home;
        }

        static void Retint(GameObject body)
        {
            foreach (var t in body.GetComponentsInChildren<ColorTinterBase>(true))
                try { t.ReapplyTint(); } catch { }
        }

        static string BodyName(GameObject go)
        {
            var n = go.name;
            int i = n.IndexOf("(Clone)", StringComparison.Ordinal);
            return (i >= 0 ? n.Substring(0, i) : n).Trim();
        }

        /// <summary>A new run: forget bodies from the last one (their sprites may be gone).</summary>
        internal static void ResetRun()
        {
            On.Clear();
            s_bodies.Clear();
        }

        static void Purge()
        {
            On.RemoveWhere(s => s == null);
            List<GameObject> dead = null;
            foreach (var k in s_bodies.Keys) if (k == null) (dead = dead ?? new List<GameObject>()).Add(k);
            if (dead != null) foreach (var k in dead) s_bodies.Remove(k);
        }

        // ------------------------------------------------------------------ atlases
        /// <summary>The silver counterpart of an atlas, or null (cached either way).</summary>
        internal static Map MapFor(exAtlas a)
        {
            if (a == null || s_silver.Contains(a) || s_none.Contains(a)) return null;
            Map m;
            if (s_maps.TryGetValue(a, out m)) return m;
            m = null;
            try
            {
                var sh = SpriteSheets.ByAtlas(a);
                if (sh != null) m = ForSheet(sh, a);
                else if (a.name == "AtlasEnemies") m = ForVanilla(a);
            }
            catch (Exception e) { Plugin.Log.LogError("Silver variant for " + a.name + " failed: " + e); m = null; }
            if (m == null) s_none.Add(a);
            else { s_maps[a] = m; s_silver.Add(m.silver); }
            return m;
        }

        static Map ForSheet(SpriteSheet sh, exAtlas a)
        {
            if (sh.id.StartsWith(Prefix)) return null;
            var id = Prefix + sh.id;
            if (!File.Exists(SpriteSheets.PathOf(id + ".png")) || !File.Exists(SpriteSheets.PathOf(id + ".json"))) return null;
            var sv = SpriteSheets.Get(id);
            if (sv == null || sv.atlas == null) return null;
            var mo = sh.manifest; var ms = sv.manifest;
            if (ms.cellW != mo.cellW || ms.cellH != mo.cellH || ms.cols != mo.cols || sv.atlas.elements.Length != a.elements.Length
                || sv.atlas.texture.width != a.texture.width || sv.atlas.texture.height != a.texture.height)
            {
                Plugin.Log.LogWarning("Silver variant " + id + " no longer matches " + sh.id + " (re-run tools/sprites/silver_variants.py): tint used");
                return null;
            }
            return new Map { silver = sv.atlas };
        }

        static Map ForVanilla(exAtlas vanilla)
        {
            var png = SpriteSheets.PathOf(VanillaSheet + ".png");
            var man = SpriteSheets.PathOf(VanillaSheet + ".json");
            if (!File.Exists(png) || !File.Exists(man)) { Plugin.Log.LogWarning("Silver variants: " + VanillaSheet + " missing"); return null; }
            var j = MiniJson.Parse(File.ReadAllText(man)) as Dictionary<string, object>;
            if (j == null || (string)j["atlas"] != vanilla.name) return null;
            int n = vanilla.elements.Length;
            if (Convert.ToInt32(j["elementCount"]) != n)
            {
                Plugin.Log.LogWarning("Silver variants: vanilla " + vanilla.name + " has " + n + " elements, the art expects " + j["elementCount"] + ": tint used");
                return null;
            }
            var tex = new Texture2D(2, 2, TextureFormat.ARGB32, false);
            tex.LoadImage(File.ReadAllBytes(png));
            tex.filterMode = FilterMode.Point;
            tex.wrapMode = TextureWrapMode.Clamp;
            tex.name = "Mod_" + VanillaSheet;
            SpriteSheets.Keep(tex);
            float W = tex.width, H = tex.height;
            var elems = new exAtlas.Element[n];
            for (int i = 0; i < n; i++)
            {
                var v = vanilla.elements[i];
                elems[i] = new exAtlas.Element { name = v.name, originalWidth = v.originalWidth, originalHeight = v.originalHeight, trimRect = v.trimRect, coords = new Rect(0, 0, 0, 0), rotated = v.rotated };
            }
            var map = new Map { has = new bool[n], bodies = new HashSet<string>() };
            var mons = j.ContainsKey("monsters") ? j["monsters"] as Dictionary<string, object> : null;
            if (mons != null) foreach (var k in mons.Keys) map.bodies.Add(k);
            int count = 0;
            foreach (var o in (List<object>)j["elements"])
            {
                var r = (List<object>)o;
                int idx = Convert.ToInt32(r[0]);
                if (idx < 0 || idx >= n) continue;
                float x = Convert.ToSingle(r[1]), y = Convert.ToSingle(r[2]), w = Convert.ToSingle(r[3]), h = Convert.ToSingle(r[4]);
                float tx = Convert.ToSingle(r[5]), ty = Convert.ToSingle(r[6]);
                var e = elems[idx];
                e.trimRect = new Rect(tx, ty, w, h);                       // ex2D: y from the top of the original cell
                e.coords = new Rect(x / W, (H - y - h) / H, w / W, h / H);  // uv origin bottom-left
                e.rotated = false;
                map.has[idx] = true;
                count++;
            }
            var atlas = ScriptableObject.CreateInstance<exAtlas>();
            atlas.name = vanilla.name + "_" + VanillaSheet;
            atlas.texture = tex;
            atlas.elements = elems;
            var mat = new Material(vanilla.material) { name = "ModMat_" + VanillaSheet, mainTexture = tex };
            atlas.material = mat;
            SpriteSheets.Keep(atlas);
            SpriteSheets.Keep(mat);
            map.silver = atlas;
            Plugin.Log.LogInfo("Loaded silver variants of vanilla finals: " + count + " frames of " + vanilla.name);
            return map;
        }

        // ------------------------------------------------------------------ checks
        /// <summary>Every tier-3 final (evolve cost 4+, not a silver unique) has a matching silver sheet; the vanilla one loads.</summary>
        public static void SelfCheck(Action<string> bad)
        {
            // reads only the json and the png header: the silver textures load on first ascension, not at every launch
            int ok = 0;
            foreach (var kv in MonsterFactory.Built)
            {
                var p = kv.Value;
                if (p == null) continue;
                float cost = 0f;
                try { cost = R.Get<float>(p, "m_evolveCost"); } catch { }
                if (cost < 4f || SilverUniques.Ids.Contains(kv.Key) || SilverUniques.Ids.Contains("Mod" + kv.Key)) continue;
                var spr = p.GetComponent<exSprite>();
                var sh = spr != null ? SpriteSheets.ByAtlas(spr.atlas) : null;
                if (sh == null) continue;
                string why = LightCheck(sh, spr.atlas);
                if (why != null) bad("silver variant for " + kv.Key + " (" + sh.id + "): " + why);
                else ok++;
            }
            foreach (var a in Resources.FindObjectsOfTypeAll<exAtlas>())
                if (a.name == "AtlasEnemies")
                {
                    try
                    {
                        var man = SpriteSheets.PathOf(VanillaSheet + ".json");
                        if (!File.Exists(man) || !File.Exists(SpriteSheets.PathOf(VanillaSheet + ".png"))) { bad("silver variants of the vanilla finals missing"); break; }
                        var j = MiniJson.Parse(File.ReadAllText(man)) as Dictionary<string, object>;
                        if (j == null || Convert.ToInt32(j["elementCount"]) != a.elements.Length) bad("silver variants of the vanilla finals no longer match " + a.name);
                    }
                    catch (Exception e) { bad("silver variants of the vanilla finals: " + e.Message); }
                    break;
                }
            if (ok == 0) bad("no silver variants found");
        }

        static string LightCheck(SpriteSheet sh, exAtlas a)
        {
            var id = Prefix + sh.id;
            string png = SpriteSheets.PathOf(id + ".png"), man = SpriteSheets.PathOf(id + ".json");
            if (!File.Exists(png) || !File.Exists(man)) return "missing";
            var j = MiniJson.Parse(File.ReadAllText(man)) as Dictionary<string, object>;
            if (j == null) return "unreadable json";
            var mo = sh.manifest;
            if (Convert.ToInt32(j["cellW"]) != mo.cellW || Convert.ToInt32(j["cellH"]) != mo.cellH || Convert.ToInt32(j["cols"]) != mo.cols) return "grid differs (stale)";
            var head = new byte[24];
            using (var f = File.OpenRead(png)) if (f.Read(head, 0, 24) < 24) return "bad png";
            int w = (head[16] << 24) | (head[17] << 16) | (head[18] << 8) | head[19];
            int h = (head[20] << 24) | (head[21] << 16) | (head[22] << 8) | head[23];
            if (a.texture != null && (w != a.texture.width || h != a.texture.height)) return "size " + w + "x" + h + " differs (stale)";
            return null;
        }
    }

    /// <summary>A sprite wearing silver: every frame its animation sets from an original atlas comes from the silver one.</summary>
    [HarmonyPatch(typeof(exSprite), "SetSprite", new[] { typeof(exAtlas), typeof(int), typeof(bool) })]
    static class Patch_SilverVariantFrames
    {
        static void Prefix(exSprite __instance, ref exAtlas _atlas, int _index)
        {
            if (SilverVariants.On.Count == 0 || _atlas == null || !SilverVariants.On.Contains(__instance)) return;
            try
            {
                var m = SilverVariants.MapFor(_atlas);
                if (m != null && m.Has(_index)) _atlas = m.silver;
            }
            catch (Exception e) { Plugin.Log.LogError("Silver variant frame: " + e); }
        }
    }
}
