using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Ghosts
{
    using CrawlFurther.Art;
    using CrawlFurther.Compat;
    using CrawlFurther.Util;

    /// <summary>
    /// The join screen's controls pictures with the ghost button drawn in: the button picked out in blue on the device,
    /// a line, and a "Ghost" row under Special, in the pictures' own style.
    /// <para>The pictures are the game's (AtlasMenuConnect, controller_diagrams_04 to _09). No copy of them ships with the
    /// mod: art/ControlDiagrams.json lists paint steps (tools/sprites/control_diagrams.py writes it) that run here on a
    /// copy of the game's own texture. Steps work in the element's trimmed pixels, x right and y down:
    /// copy (src x,y,w,h to dst x,y, optional colour map, "move" clears the source first), recolor (rect and map),
    /// clear (rect, optional colours: those pixels become transparent) and pixels (one colour at a list of points).</para>
    /// <para>The redrawn pictures play as clips of their own beside the game's (the game's clips are untouched), and only
    /// for a player whose ghost button is the one drawn (<see cref="GhostControls.IsPictured"/>); anyone else keeps the
    /// game's picture and the text line under it.</para>
    /// </summary>
    public static class ControlDiagrams
    {
        const string File = "ControlDiagrams.json";
        const string ClipSuffix = "_ModGhost";
        const int Tolerance = 4;

        static bool s_built;
        static exAtlas s_atlas;
        static exAtlas s_vanilla;
        static readonly Dictionary<string, int> s_index = new Dictionary<string, int>();          // element name -> our index
        static readonly Dictionary<string, exSpriteAnimClip> s_clips = new Dictionary<string, exSpriteAnimClip>();

        /// <summary>
        /// After the game has played its controls clip on <paramref name="diagram"/>: plays the redrawn one instead when
        /// there is one for that picture and the player's ghost button is the one it shows. True when it did.
        /// </summary>
        public static bool Apply(exSpriteAnimation diagram, PlayerData pd)
        {
            try
            {
                if (diagram == null || pd == null || pd.IsBot) return false;
                var st = diagram.GetCurrentAnimation();
                var clip = st != null ? st.clip : null;
                if (clip == null || clip.name.EndsWith(ClipSuffix, StringComparison.Ordinal)) return false;
                if (!GhostControls.IsPictured((int)pd.ControllerId)) return false;
                var ours = Redrawn(clip);
                if (ours == null) return false;
                diagram.Play(ours);
                return true;
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Controls picture: " + e.Message); return false; }
        }

        /// <summary>The redrawn copy of a controls clip, or null when its picture has no steps (or the art failed).</summary>
        static exSpriteAnimClip Redrawn(exSpriteAnimClip clip)
        {
            exSpriteAnimClip c;
            if (s_clips.TryGetValue(clip.name, out c)) return c;
            s_clips[clip.name] = null;
            if (clip.frameInfos == null || clip.frameInfos.Count == 0) return null;
            var f0 = clip.frameInfos[0];
            if (f0.atlas == null) return null;
            Build(f0.atlas);
            if (s_atlas == null || f0.atlas != s_vanilla) return null;
            var frames = new List<exSpriteAnimClip.FrameInfo>();
            foreach (var f in clip.frameInfos)
            {
                int idx;
                string name = f.atlas == s_vanilla && f.index >= 0 && f.index < s_vanilla.elements.Length ? s_vanilla.elements[f.index].name : null;
                if (name == null || !s_index.TryGetValue(name, out idx)) return null;
                frames.Add(new exSpriteAnimClip.FrameInfo { atlas = s_atlas, index = idx, length = f.length, textureGUID = "" });
            }
            c = UnityEngine.Object.Instantiate(clip);
            c.name = clip.name + ClipSuffix;
            c.frameInfos = frames;
            SpriteSheets.Keep(c);
            s_clips[clip.name] = c;
            return c;
        }

        /// <summary>Runs the steps on a copy of the pictures' atlas once, packing the results into an atlas of ours.</summary>
        static void Build(exAtlas vanilla)
        {
            if (s_built) return;
            s_built = true;
            var path = SpriteSheets.PathOf(File);
            if (!System.IO.File.Exists(path)) { FurtherCore.Log.LogWarning("Controls pictures: " + path + " missing"); return; }
            var root = MiniJson.Parse(System.IO.File.ReadAllText(path)) as Dictionary<string, object>;
            if (root == null) return;
            object an; object fr;
            if (!root.TryGetValue("atlas", out an) || (string)an != vanilla.name || !root.TryGetValue("frames", out fr)) return;
            var frames = fr as Dictionary<string, object>;
            if (frames == null || vanilla.texture == null) return;

            var src = SpriteUtil.CopyTexture(vanilla.texture);
            var px = src.GetPixels32(0);
            int W = src.width, H = src.height;
            UnityEngine.Object.Destroy(src);

            var made = new List<KeyValuePair<exAtlas.Element, Color32[]>>();
            foreach (var kv in frames)
            {
                int ei = Array.FindIndex(vanilla.elements, e => e.name == kv.Key);
                if (ei < 0 || vanilla.elements[ei].rotated) { FurtherCore.Log.LogWarning("Controls pictures: no element " + kv.Key); continue; }
                var el = vanilla.elements[ei];
                int cw = el.originalWidth, ch = el.originalHeight;
                var cv = new Color32[cw * ch];
                int ox = Mathf.RoundToInt(el.trimRect.x), oy = Mathf.RoundToInt(el.trimRect.y);
                int tx = Mathf.RoundToInt(el.coords.x * W), ty = Mathf.RoundToInt(el.coords.y * H);
                int tw = Mathf.RoundToInt(el.coords.width * W), th = Mathf.RoundToInt(el.coords.height * H);
                for (int j = 0; j < th; j++)
                    for (int i = 0; i < tw; i++)
                    {
                        int x = ox + i, y = oy + j;
                        if (x < 0 || y < 0 || x >= cw || y >= ch) continue;
                        cv[y * cw + x] = px[(ty + th - 1 - j) * W + tx + i];
                    }
                var steps = kv.Value as List<object>;
                if (steps != null)
                    foreach (var s in steps) Run(s as Dictionary<string, object>, cv, cw, ch, ox, oy);
                made.Add(new KeyValuePair<exAtlas.Element, Color32[]>(el, cv));
            }
            if (made.Count == 0) return;

            // pack side by side, each canvas at the top
            int TW = 0, TH = 0;
            foreach (var m in made) { TW += m.Key.originalWidth + 1; TH = Math.Max(TH, m.Key.originalHeight); }
            var outp = new Color32[TW * TH];
            var elems = new exAtlas.Element[made.Count];
            int at = 0;
            for (int k = 0; k < made.Count; k++)
            {
                var el = made[k].Key; var cv = made[k].Value;
                int cw = el.originalWidth, ch = el.originalHeight;
                int minX = cw, minY = ch, maxX = -1, maxY = -1;
                for (int y = 0; y < ch; y++)
                    for (int x = 0; x < cw; x++)
                    {
                        var p = cv[y * cw + x];
                        if (p.a == 0) continue;
                        outp[(TH - 1 - y) * TW + at + x] = p;
                        if (x < minX) minX = x; if (x > maxX) maxX = x; if (y < minY) minY = y; if (y > maxY) maxY = y;
                    }
                if (maxX < 0) { minX = minY = 0; maxX = maxY = 0; }
                int bw = maxX - minX + 1, bh = maxY - minY + 1;
                elems[k] = new exAtlas.Element
                {
                    name = el.name, originalWidth = cw, originalHeight = ch, rotated = false,
                    trimRect = new Rect(minX, minY, bw, bh),
                    coords = new Rect((float)(at + minX) / TW, (float)(TH - 1 - maxY) / TH, (float)bw / TW, (float)bh / TH),
                };
                s_index[el.name] = k;
                at += cw + 1;
            }
            var tex = new Texture2D(TW, TH, TextureFormat.ARGB32, false)
            {
                filterMode = FilterMode.Point, wrapMode = TextureWrapMode.Clamp,
                name = OnlineNames.ComposedTexture("ControlDiagrams", FurtherCore.VERSION),
            };
            tex.SetPixels32(outp);
            tex.Apply(false);
            s_atlas = SpriteUtil.MakeAtlas(OnlineNames.Atlas("ControlDiagrams"), tex, elems, vanilla.material);
            s_vanilla = vanilla;
            FurtherCore.Log.LogInfo("Controls pictures: " + made.Count + " redrawn with the ghost button");
        }

        static void Run(Dictionary<string, object> st, Color32[] cv, int cw, int ch, int ox, int oy)
        {
            if (st == null) return;
            string op = Str(st, "op");
            Func<int, int, bool> inside = (x, y) => x + ox >= 0 && y + oy >= 0 && x + ox < cw && y + oy < ch;
            Func<int, int, int> at = (x, y) => (y + oy) * cw + x + ox;
            switch (op)
            {
                case "copy":
                {
                    var s = Ints(st, "src"); var d = Ints(st, "dst"); var map = Map(st, "map");
                    if (s == null || d == null || s.Length < 4 || d.Length < 2) return;
                    var snap = new Color32[s[2] * s[3]];
                    var have = new bool[s[2] * s[3]];
                    for (int j = 0; j < s[3]; j++)
                        for (int i = 0; i < s[2]; i++)
                            if (inside(s[0] + i, s[1] + j)) { snap[j * s[2] + i] = cv[at(s[0] + i, s[1] + j)]; have[j * s[2] + i] = true; }
                    if (Bool(st, "move"))
                        for (int j = 0; j < s[3]; j++)
                            for (int i = 0; i < s[2]; i++)
                                if (have[j * s[2] + i]) cv[at(s[0] + i, s[1] + j)] = new Color32(0, 0, 0, 0);
                    for (int j = 0; j < s[3]; j++)
                        for (int i = 0; i < s[2]; i++)
                        {
                            var p = snap[j * s[2] + i];
                            if (!have[j * s[2] + i] || p.a == 0 || !inside(d[0] + i, d[1] + j)) continue;
                            cv[at(d[0] + i, d[1] + j)] = Swap(p, map);
                        }
                    break;
                }
                case "recolor":
                case "clear":
                {
                    var r = Ints(st, "rect");
                    if (r == null || r.Length < 4) return;
                    var map = op == "recolor" ? Map(st, "map") : null;
                    var only = op == "clear" ? Colors(st, "colors") : null;
                    for (int j = 0; j < r[3]; j++)
                        for (int i = 0; i < r[2]; i++)
                        {
                            if (!inside(r[0] + i, r[1] + j)) continue;
                            int k = at(r[0] + i, r[1] + j);
                            var p = cv[k];
                            if (p.a == 0) continue;
                            if (op == "recolor") cv[k] = Swap(p, map);
                            else if (only == null || only.Count == 0 || only.Exists(c => Near(p, c))) cv[k] = new Color32(0, 0, 0, 0);
                        }
                    break;
                }
                case "pixels":
                {
                    var col = ColorOf(st, "color");
                    object o;
                    if (!st.TryGetValue("pts", out o)) return;
                    var pts = o as List<object>;
                    if (pts == null) return;
                    foreach (var q in pts)
                    {
                        var xy = q as List<object>;
                        if (xy == null || xy.Count < 2) continue;
                        int x = Convert.ToInt32(xy[0]), y = Convert.ToInt32(xy[1]);
                        if (inside(x, y)) cv[at(x, y)] = col;
                    }
                    break;
                }
            }
        }

        static bool Near(Color32 a, Color32 b)
        {
            return Math.Abs(a.r - b.r) <= Tolerance && Math.Abs(a.g - b.g) <= Tolerance && Math.Abs(a.b - b.b) <= Tolerance;
        }

        static Color32 Swap(Color32 p, List<KeyValuePair<Color32, Color32>> map)
        {
            if (map != null)
                foreach (var m in map)
                    if (Near(p, m.Key)) return new Color32(m.Value.r, m.Value.g, m.Value.b, p.a);
            return p;
        }

        static string Str(Dictionary<string, object> d, string k) { object o; return d.TryGetValue(k, out o) ? o as string : null; }
        static bool Bool(Dictionary<string, object> d, string k) { object o; return d.TryGetValue(k, out o) && o is bool && (bool)o; }

        static int[] Ints(Dictionary<string, object> d, string k)
        {
            object o;
            if (!d.TryGetValue(k, out o)) return null;
            var l = o as List<object>;
            if (l == null) return null;
            var r = new int[l.Count];
            for (int i = 0; i < l.Count; i++) r[i] = Convert.ToInt32(l[i]);
            return r;
        }

        static Color32 ToColor(object o)
        {
            var l = o as List<object>;
            if (l == null || l.Count < 3) return new Color32(255, 0, 255, 255);
            return new Color32((byte)Convert.ToInt32(l[0]), (byte)Convert.ToInt32(l[1]), (byte)Convert.ToInt32(l[2]), 255);
        }

        static Color32 ColorOf(Dictionary<string, object> d, string k) { object o; return d.TryGetValue(k, out o) ? ToColor(o) : new Color32(255, 0, 255, 255); }

        static List<Color32> Colors(Dictionary<string, object> d, string k)
        {
            object o;
            var r = new List<Color32>();
            if (!d.TryGetValue(k, out o) || !(o is List<object>)) return r;
            foreach (var c in (List<object>)o) r.Add(ToColor(c));
            return r;
        }

        static List<KeyValuePair<Color32, Color32>> Map(Dictionary<string, object> d, string k)
        {
            object o;
            if (!d.TryGetValue(k, out o) || !(o is List<object>)) return null;
            var r = new List<KeyValuePair<Color32, Color32>>();
            foreach (var pair in (List<object>)o)
            {
                var p = pair as List<object>;
                if (p != null && p.Count >= 2) r.Add(new KeyValuePair<Color32, Color32>(ToColor(p[0]), ToColor(p[1])));
            }
            return r;
        }
    }
}
