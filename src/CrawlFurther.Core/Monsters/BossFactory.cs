using System;
using System.Collections.Generic;
using System.IO;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Monsters
{
    using CrawlFurther.Art;
    using CrawlFurther.Compat;
    using CrawlFurther.Util;

    /// <summary>
    /// New bosses built from a vanilla boss's machinery (rooms, phases, possessable parts). The usual order:
    /// <see cref="LoadArt"/> the redrawn atlas, <see cref="RecolorClone"/> the vanilla boss prefab (every frame it draws
    /// is swapped for its redrawn counterpart, or repainted through a colour transform when the art is missing),
    /// <see cref="Relink"/>, replace its attacks, then add the Boss to <see cref="Built"/> (and its art to
    /// <see cref="ArtOf"/>). Built bosses join the boss rotation: <see cref="Chance"/> of boss fights pick one.
    /// </summary>
    public static class BossFactory
    {
        /// <summary>Mod bosses in the rotation. Add yours once it is built.</summary>
        public static readonly List<Boss> Built = new List<Boss>();
        /// <summary>The redrawn art each mod boss wears, shown on the lose scene when that boss wins.</summary>
        public static readonly Dictionary<Boss, BossArt> ArtOf = new Dictionary<Boss, BossArt>();
        /// <summary>When set, every boss fight picks this boss (a dev key cycles it for testing).</summary>
        public static Boss Forced;
        /// <summary>Share of boss fights that pick a mod boss (0..1). One roll per game: a retry keeps the same boss.</summary>
        public static float Chance = 0.4f;

        static readonly Dictionary<string, exAtlas> s_atlas = new Dictionary<string, exAtlas>();

        /// <summary>The loaded vanilla atlas named <paramref name="name"/> (e.g. "AtlasBoss"), or null.</summary>
        public static exAtlas VanillaAtlas(string name)
        {
            foreach (var a in Resources.FindObjectsOfTypeAll<exAtlas>()) if (a.name == name) return a;
            return null;
        }

        /// <summary>
        /// Load &lt;sheet&gt;.png + .json from the art folders as a mod atlas parallel to <paramref name="vanilla"/>. The json
        /// names the atlas, its element count and one row per redrawn element: [index, x, y, w, h, trimX, trimY] (pixels,
        /// y down). Returns null (and logs) when the files are missing or are for another atlas.
        /// </summary>
        public static BossArt LoadArt(string sheet, exAtlas vanilla)
        {
            try
            {
                if (vanilla == null) return null;
                var png = SpriteSheets.PathOf(sheet + ".png");
                var man = SpriteSheets.PathOf(sheet + ".json");
                if (!File.Exists(png) || !File.Exists(man)) { FurtherCore.Log.LogWarning("Boss art missing: " + png); return null; }
                var j = MiniJson.Parse(File.ReadAllText(man)) as Dictionary<string, object>;
                if (j == null || (string)j["atlas"] != vanilla.name)
                {
                    FurtherCore.Log.LogWarning("Boss art " + sheet + " is not for " + vanilla.name); return null;
                }
                int n = vanilla.elements.Length;
                if (Convert.ToInt32(j["elementCount"]) != n)
                    FurtherCore.Log.LogWarning("Boss art " + sheet + ": vanilla " + vanilla.name + " has " + n + " elements, art expects " + j["elementCount"]);
                var tex = new Texture2D(2, 2, TextureFormat.ARGB32, false);
                tex.LoadImage(File.ReadAllBytes(png));
                tex.filterMode = FilterMode.Point;
                tex.wrapMode = TextureWrapMode.Clamp;
                tex.name = OnlineNames.SheetTexture(sheet);
                float W = tex.width, H = tex.height;
                var elems = new exAtlas.Element[n];
                for (int i = 0; i < n; i++)
                {
                    var v = vanilla.elements[i];
                    elems[i] = new exAtlas.Element { name = v.name, originalWidth = v.originalWidth, originalHeight = v.originalHeight, trimRect = v.trimRect, coords = v.coords, rotated = v.rotated };
                }
                var art = new BossArt { sheet = sheet, vanillaName = vanilla.name, has = new bool[n] };
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
                    art.has[idx] = true;
                    art.count++;
                }
                art.atlas = SpriteUtil.MakeAtlas(OnlineNames.Atlas(sheet), tex, elems, vanilla.material);
                art.atlas.material.name = OnlineNames.Material(sheet);
                FurtherCore.Log.LogInfo("Loaded boss art " + sheet + ": " + art.count + " redrawn frames of " + vanilla.name + " (" + tex.width + "x" + tex.height + ")");
                return art;
            }
            catch (Exception e) { FurtherCore.Log.LogError("Boss art " + sheet + " failed: " + e); return null; }
        }

        /// <summary>
        /// Clone a vanilla prefab and reskin everything it draws from <paramref name="atlases"/>: with the redrawn
        /// <paramref name="art"/>, or through <paramref name="paint"/> (a colour transform, cached per <paramref name="key"/>)
        /// when art is null. <paramref name="shared"/> collects every original -> copy made, for <see cref="Relink"/>.
        /// </summary>
        public static GameObject RecolorClone(GameObject prefab, string newName, string key, Func<Color32, Color32> paint,
                                              HashSet<string> atlases, Dictionary<UnityEngine.Object, UnityEngine.Object> shared,
                                              BossArt art = null, int depth = 0)
        {
            var clone = MonsterFactory.ClonePrefab(prefab, newName);
            shared[prefab] = clone;
            Reskin(clone, key, paint, atlases, shared, art, depth);
            return clone;
        }

        /// <summary>
        /// Point every clip of <paramref name="clone"/> (and of the prefabs it spawns, two levels deep) at the redrawn
        /// art (or a repainted atlas when <paramref name="art"/> is null). Clips are copied, never edited in place.
        /// </summary>
        public static void Reskin(GameObject clone, string key, Func<Color32, Color32> paint, HashSet<string> atlases,
                                  Dictionary<UnityEngine.Object, UnityEngine.Object> shared, BossArt art = null, int depth = 0)
        {
            var clips = new HashSet<exSpriteAnimClip>();
            var externals = new HashSet<GameObject>();
            R.VisitReferences(clone, o =>
            {
                var c = o as exSpriteAnimClip;
                if (c != null) { clips.Add(c); return null; }
                var g = o as GameObject;
                if (g != null && !g.transform.IsChildOf(clone.transform) && !g.scene.IsValid() && g.GetComponent<Room>() == null) externals.Add(g);
                return null;
            });
            foreach (var c in clips)
            {
                if (shared.ContainsKey(c)) continue;
                bool uses = false;
                foreach (var f in c.frameInfos)
                    if (f.atlas != null && atlases.Contains(f.atlas.name) && (art == null || art.Has(f.atlas, f.index))) { uses = true; break; }
                if (!uses) continue;
                var nc = UnityEngine.Object.Instantiate(c);
                nc.name = c.name;   // animation components look clips up by name
                SpriteSheets.Keep(nc);
                foreach (var f in nc.frameInfos)
                {
                    if (f.atlas == null || !atlases.Contains(f.atlas.name)) continue;
                    if (art != null) { if (art.Has(f.atlas, f.index)) f.atlas = art.atlas; }
                    else f.atlas = Painted(f.atlas, key, paint);
                }
                shared[c] = nc;
            }
            if (art == null)
                foreach (var a in Resources.FindObjectsOfTypeAll<exAtlas>())
                    if (atlases.Contains(a.name) && !shared.ContainsKey(a)) shared[a] = Painted(a, key, paint);
            if (depth < 2)
                foreach (var g in externals)
                    if (!shared.ContainsKey(g) && UsesAtlas(g, atlases, art))
                        RecolorClone(g, g.name + "_" + key, key, paint, atlases, shared, art, depth + 1);
        }

        /// <summary>After all clones exist, point every clone at the repainted clips, atlases and cloned prefabs.</summary>
        public static void Relink(Dictionary<UnityEngine.Object, UnityEngine.Object> shared, BossArt art = null)
        {
            // repoint sprites first: SetSprite only swaps the renderer's material when the atlas changes,
            // so it must run while the sprite still holds the vanilla atlas
            foreach (var kv in shared)
            {
                var g = kv.Value as GameObject;
                if (g == null) continue;
                foreach (var s in g.GetComponentsInChildren<exSprite>(true))
                {
                    UnityEngine.Object na;
                    if (art != null && art.Has(s.atlas, s.index))
                    {
                        s.SetSprite(art.atlas, s.index);
                        var r = s.GetComponent<Renderer>();
                        if (r != null && art.atlas.material != null) r.sharedMaterial = art.atlas.material;
                    }
                    else if (s.atlas != null && shared.TryGetValue(s.atlas, out na))
                    {
                        var pa = (exAtlas)na;
                        s.SetSprite(pa, s.index);
                        var r = s.GetComponent<Renderer>();
                        if (r != null && pa.material != null) r.sharedMaterial = pa.material;
                    }
                }
            }
            foreach (var kv in shared)
            {
                var g = kv.Value as GameObject;
                if (g != null) R.RemapReferences(g, shared);
            }
        }

        /// <summary>
        /// Does a prefab draw anything we reskin? With redrawn art: any frame that was redrawn, here or in a prefab it
        /// spawns one level down (so a dropper whose puddle was redrawn is cloned too).
        /// </summary>
        static bool UsesAtlas(GameObject g, HashSet<string> atlases, BossArt art = null, int look = 1)
        {
            foreach (var s in g.GetComponentsInChildren<exSprite>(true))
                if (s.atlas != null && atlases.Contains(s.atlas.name) && (art == null || art.Has(s.atlas, s.index))) return true;
            foreach (var a in g.GetComponentsInChildren<exSpriteAnimation>(true))
                foreach (var c in a.animations)
                    if (c != null)
                        foreach (var f in c.frameInfos)
                            if (f.atlas != null && atlases.Contains(f.atlas.name) && (art == null || art.Has(f.atlas, f.index))) return true;
            bool found = false;
            if (art != null && look > 0)
                R.VisitReferences(g, o =>
                {
                    if (found) return null;
                    var c = o as exSpriteAnimClip;
                    if (c != null)
                    {
                        foreach (var f in c.frameInfos) if (art.Has(f.atlas, f.index)) { found = true; break; }
                        return null;
                    }
                    var gg = o as GameObject;
                    if (gg != null && gg != g && !gg.scene.IsValid() && !gg.transform.IsChildOf(g.transform) && gg.GetComponent<Room>() == null
                        && UsesAtlas(gg, atlases, art, look - 1)) found = true;
                    return null;
                });
            return found;
        }

        /// <summary>
        /// Second pass for a boss whose effect chains also draw from another vanilla atlas (the shared effects atlas):
        /// reskin the boss and every clone made so far against that atlas's redrawn art, then relink.
        /// </summary>
        public static void ReskinAll(GameObject boss, Dictionary<UnityEngine.Object, UnityEngine.Object> shared, BossArt art)
        {
            if (art == null) return;
            var set = new HashSet<string> { art.vanillaName };
            var roots = new List<GameObject> { boss };
            foreach (var v in shared.Values) { var g = v as GameObject; if (g != null && !roots.Contains(g)) roots.Add(g); }
            foreach (var g in roots) Reskin(g, art.sheet, null, set, shared, art, 0);
            Relink(shared, art);
        }

        /// <summary>A copy of <paramref name="src"/> with every colour passed through <paramref name="paint"/>, cached per key.</summary>
        public static exAtlas Painted(exAtlas src, string key, Func<Color32, Color32> paint)
        {
            exAtlas a;
            var k = src.name + "|" + key;
            if (s_atlas.TryGetValue(k, out a) && a != null) return a;
            var tex = SpriteUtil.CopyTexture(src.texture);
            tex.name = OnlineNames.ComposedTexture(src.name, key);   // the same transform of the same atlas: the same pixels
            var px = tex.GetPixels32();
            var cache = new Dictionary<int, Color32>();
            for (int i = 0; i < px.Length; i++)
            {
                var c = px[i];
                if (c.a == 0) continue;
                int id = (c.r << 16) | (c.g << 8) | c.b;
                Color32 o;
                if (!cache.TryGetValue(id, out o)) { o = paint(c); cache[id] = o; }
                px[i] = new Color32(o.r, o.g, o.b, c.a);
            }
            tex.SetPixels32(px);
            tex.Apply(false);
            a = SpriteUtil.MakeAtlas(OnlineNames.Atlas(src.name + "_" + key), tex, src.elements, src.material);
            a.material.name = OnlineNames.Material(src.name + "_" + key);
            s_atlas[k] = a;
            FurtherCore.Log.LogInfo("Repainted atlas " + src.name + " for " + key + " (" + cache.Count + " colours)");
            return a;
        }

        // ------------------------------------------------------------------ colour helpers for paint transforms
        /// <summary>A colour from hue (degrees, wrapped), saturation and value (0..1, clamped).</summary>
        public static Color32 HSV(float h, float s, float v, byte a = 255)
        {
            var c = Color.HSVToRGB(Mathf.Repeat(h, 360f) / 360f, Mathf.Clamp01(s), Mathf.Clamp01(v));
            return new Color32((byte)(c.r * 255), (byte)(c.g * 255), (byte)(c.b * 255), a);
        }

        /// <summary>Hue (degrees), saturation and value (0..1) of a colour.</summary>
        public static void ToHSV(Color32 c, out float h, out float s, out float v)
        {
            Color.RGBToHSV(c, out h, out s, out v);
            h *= 360f;
        }
    }

    /// <summary>
    /// Mod bosses join the rotation: <see cref="BossFactory.Chance"/> of boss fights pick one of them. Runs after every
    /// other boss mod's postfix and replaces only a vanilla pick, so a boss another mod chose for the run stays
    /// (<see cref="CompatBosses"/>).
    /// </summary>
    [HarmonyPatch(typeof(SystemGame), "CalcNextBoss")]
    [HarmonyPriority(Priority.Last)]
    [HarmonyAfter(CompatBosses.KitGuid, CompatBosses.LabyrinthGuid)]
    static class Patch_CalcNextBoss
    {
        static int s_key = int.MinValue;
        static Boss s_pick;

        static void Postfix(ref Boss __result)
        {
            try
            {
                if (BossFactory.Built.Count == 0 || SystemGame.GetIsTutorialMatch()) return;
                if (BossFactory.Forced != null) { __result = BossFactory.Forced; return; }
                if (!CompatBosses.IsVanillaBoss(__result)) return;
                // one roll per game: retrying the boss keeps the same boss
                int key = (int)R.Get<ShuffledIndex>(Singleton<SystemGame>.Get, "m_bossOrder");
                if (key != s_key)
                {
                    s_key = key;
                    s_pick = UnityEngine.Random.value < BossFactory.Chance ? BossFactory.Built[UnityEngine.Random.Range(0, BossFactory.Built.Count)] : null;
                }
                if (s_pick != null) __result = s_pick;
            }
            catch (Exception e) { FurtherCore.Log.LogError("Boss pick failed: " + e); }
        }
    }
}
