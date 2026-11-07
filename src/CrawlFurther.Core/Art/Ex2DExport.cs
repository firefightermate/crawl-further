using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using UnityEngine;

namespace CrawlFurther.Art
{
    using CrawlFurther.Util;

    /// <summary>
    /// Writes the game's ex2D art (vanilla or modded) to files: any exAtlas to a PNG plus JSON in the
    /// <see cref="SheetManifest"/> format, and any exSpriteAnimClip to JSON with its frames, timings and events.
    /// An exported atlas is a normal sheet: copy its PNG and JSON into your art folder, edit them, and load the result
    /// with <see cref="SpriteSheets.Get"/>.
    /// <para>
    /// The game's atlases are packed (frames trimmed, some rotated). Export unpacks them onto a grid: every cell is as
    /// big as the atlas's largest frame, and each frame sits bottom-centred in its cell at its original size. The JSON
    /// adds, beside the manifest keys, "source" (the atlas name) and "elements" (each cell's original name and size).
    /// "anims" lists every loaded clip drawn entirely from the atlas, with its frame durations. An atlas too big for one
    /// grid texture is written packed instead, as its texture plus "packed": true and each element's rectangle.
    /// </para>
    /// From code: <c>Ex2DExport.Atlas(atlas, dir)</c>, <c>Ex2DExport.Clip(clip, dir)</c> or <c>Ex2DExport.All(dir)</c>.
    /// With DebugKeys on in BepInEx/config/CrawlMod.Debug.cfg, F8 exports everything to the plugin folder's ex2d_export.
    /// </summary>
    public static class Ex2DExport
    {
        /// <summary>
        /// Write <paramref name="atlas"/> to <paramref name="dir"/>/&lt;atlas name&gt;.png and .json. Returns the PNG's
        /// path, or null when the atlas has no texture or elements.
        /// </summary>
        public static string Atlas(exAtlas atlas, string dir)
        {
            return Atlas(atlas, dir, ClipsByAtlas());
        }

        /// <summary>Write <paramref name="clip"/> to <paramref name="dir"/>/&lt;clip name&gt;.json and return the path.</summary>
        public static string Clip(exSpriteAnimClip clip, string dir)
        {
            Directory.CreateDirectory(dir);
            var path = Path.Combine(dir, FileName(clip.name) + ".json");
            File.WriteAllText(path, MiniJson.Write(ClipJson(clip)));
            return path;
        }

        /// <summary>
        /// Export every loaded atlas to <paramref name="dir"/>/atlases and every loaded clip to <paramref name="dir"/>/clips,
        /// and list the atlases (size, format, material, shader) in <paramref name="dir"/>/index.txt. Takes a few seconds.
        /// Returns the number of files written.
        /// </summary>
        public static int All(string dir)
        {
            int files = 0;
            var byAtlas = ClipsByAtlas();
            var index = new StringBuilder();
            index.AppendLine("ex2D export " + DateTime.Now);
            var atlasDir = Path.Combine(dir, "atlases");
            foreach (var a in Resources.FindObjectsOfTypeAll<exAtlas>())
            {
                index.AppendLine(Describe(a));
                try { if (Atlas(a, atlasDir, byAtlas) != null) files += 2; }
                catch (Exception e) { FurtherCore.Log.LogWarning("Export of atlas " + a.name + " failed: " + e.Message); }
            }
            var clipDir = Path.Combine(dir, "clips");
            var used = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach (var c in Resources.FindObjectsOfTypeAll<exSpriteAnimClip>())
            {
                if (!used.Add(c.name)) continue;   // runtime copies keep their source clip's name
                try { Clip(c, clipDir); files++; }
                catch (Exception e) { FurtherCore.Log.LogWarning("Export of clip " + c.name + " failed: " + e.Message); }
            }
            Directory.CreateDirectory(dir);
            File.WriteAllText(Path.Combine(dir, "index.txt"), index.ToString());
            FurtherCore.Log.LogInfo("ex2D export: " + files + " files in " + dir);
            return files + 1;
        }

        static string Describe(exAtlas a)
        {
            var mat = a.material;
            var tex = a.texture;
            bool readable = false;
            try { if (tex != null) { tex.GetPixel(0, 0); readable = true; } } catch { }
            var sb = new StringBuilder(string.Format("{0}  elements {1}, texture {2} {3}x{4} {5}{6}, material {7}, shader {8}",
                a.name, a.elements == null ? 0 : a.elements.Length,
                tex ? tex.name : "none", tex ? tex.width : 0, tex ? tex.height : 0, tex ? tex.format.ToString() : "",
                readable ? " (readable)" : "", mat ? mat.name : "none", mat && mat.shader ? mat.shader.name : "none"));
            if (mat != null)
                foreach (var p in new[] { "_MainTex", "_ColorRamp", "_Color" })
                    if (mat.HasProperty(p)) sb.Append(", has " + p);
            return sb.ToString();
        }

        static Dictionary<exAtlas, List<exSpriteAnimClip>> ClipsByAtlas()
        {
            var d = new Dictionary<exAtlas, List<exSpriteAnimClip>>();
            foreach (var c in Resources.FindObjectsOfTypeAll<exSpriteAnimClip>())
            {
                if (c.frameInfos == null || c.frameInfos.Count == 0) continue;
                var a = c.frameInfos[0].atlas;
                if (a == null) continue;
                bool one = true;
                foreach (var f in c.frameInfos) if (f.atlas != a) { one = false; break; }
                if (!one) continue;
                List<exSpriteAnimClip> l;
                if (!d.TryGetValue(a, out l)) d[a] = l = new List<exSpriteAnimClip>();
                l.Add(c);
            }
            return d;
        }

        static string Atlas(exAtlas atlas, string dir, Dictionary<exAtlas, List<exSpriteAnimClip>> byAtlas)
        {
            var els = atlas.elements;
            if (atlas.texture == null || els == null || els.Length == 0) return null;
            Directory.CreateDirectory(dir);
            var name = FileName(atlas.name);
            var src = SpriteUtil.CopyTexture(atlas.texture);
            try
            {
                int cellW = 1, cellH = 1;
                foreach (var e in els) { cellW = Mathf.Max(cellW, e.originalWidth); cellH = Mathf.Max(cellH, e.originalHeight); }
                int max = Mathf.Min(SystemInfo.maxTextureSize, 8192);
                int cols = Mathf.Clamp(Mathf.CeilToInt(Mathf.Sqrt(els.Length * (float)cellH / cellW)), 1, Mathf.Max(1, max / cellW));
                int rows = (els.Length + cols - 1) / cols;
                var json = new Dictionary<string, object>();
                json["source"] = atlas.name;
                byte[] png;
                if (cols * cellW > max || rows * cellH > max)
                {
                    json["packed"] = true;
                    json["elements"] = PackedElements(atlas, src);
                    png = src.EncodeToPNG();
                }
                else
                {
                    json["cellW"] = cellW;
                    json["cellH"] = cellH;
                    json["cols"] = cols;
                    json["anims"] = Anims(atlas, byAtlas);
                    var cells = new List<object>();
                    foreach (var e in els) cells.Add(new Dictionary<string, object> { { "name", e.name }, { "w", e.originalWidth }, { "h", e.originalHeight } });
                    json["elements"] = cells;
                    png = Grid(src, els, cellW, cellH, cols, rows);
                }
                File.WriteAllBytes(Path.Combine(dir, name + ".png"), png);
                File.WriteAllText(Path.Combine(dir, name + ".json"), MiniJson.Write(json));
                return Path.Combine(dir, name + ".png");
            }
            finally { UnityEngine.Object.Destroy(src); }
        }

        /// <summary>The atlas unpacked onto a cols x rows grid of cellW x cellH cells, each frame bottom-centred in its cell.</summary>
        static byte[] Grid(Texture2D src, exAtlas.Element[] els, int cellW, int cellH, int cols, int rows)
        {
            int TW = src.width, TH = src.height;
            var sp = src.GetPixels32();
            int W = cols * cellW, H = rows * cellH;
            var px = new Color32[W * H];
            for (int i = 0; i < els.Length; i++)
            {
                var e = els[i];
                // the stored rectangle, bottom-up as in the texture; a rotated element is stored a quarter turn clockwise
                int x0 = Mathf.RoundToInt(e.coords.x * TW), y0 = Mathf.RoundToInt(e.coords.y * TH);
                int w = Mathf.RoundToInt(e.coords.width * TW), h = Mathf.RoundToInt(e.coords.height * TH);
                int tw = e.rotated ? h : w, th = e.rotated ? w : h;
                // where the trimmed frame lands, top-down: the original frame bottom-centred, trimRect.y counted from its top
                int left = (i % cols) * cellW + (cellW - e.originalWidth) / 2 + Mathf.RoundToInt(e.trimRect.x);
                int top = (i / cols) * cellH + (cellH - e.originalHeight) + Mathf.RoundToInt(e.trimRect.y);
                int cellLeft = (i % cols) * cellW, cellTop = (i / cols) * cellH;
                for (int ty = 0; ty < th; ty++)
                    for (int tx = 0; tx < tw; tx++)
                    {
                        int sx = e.rotated ? th - 1 - ty : tx, sy = e.rotated ? tx : ty;   // stored pixel, top-down within the rectangle
                        int srcX = x0 + sx, srcY = y0 + h - 1 - sy;
                        if (srcX < 0 || srcX >= TW || srcY < 0 || srcY >= TH) continue;
                        int X = left + tx, Y = top + ty;
                        if (X < cellLeft || X >= cellLeft + cellW || Y < cellTop || Y >= cellTop + cellH) continue;
                        px[(H - 1 - Y) * W + X] = sp[srcY * TW + srcX];
                    }
            }
            var tex = new Texture2D(W, H, TextureFormat.ARGB32, false);
            try
            {
                tex.SetPixels32(px);
                tex.Apply(false);
                return tex.EncodeToPNG();
            }
            finally { UnityEngine.Object.Destroy(tex); }
        }

        static List<object> PackedElements(exAtlas atlas, Texture2D src)
        {
            var l = new List<object>();
            foreach (var e in atlas.elements)
            {
                int w = Mathf.RoundToInt(e.coords.width * src.width), h = Mathf.RoundToInt(e.coords.height * src.height);
                l.Add(new Dictionary<string, object>
                {
                    { "name", e.name },
                    { "x", Mathf.RoundToInt(e.coords.x * src.width) },
                    { "y", src.height - Mathf.RoundToInt(e.coords.y * src.height) - h },   // from the top
                    { "w", w }, { "h", h }, { "rotated", e.rotated },
                    { "trimX", e.trimRect.x }, { "trimY", e.trimRect.y },
                    { "originalW", e.originalWidth }, { "originalH", e.originalHeight },
                });
            }
            return l;
        }

        static List<object> Anims(exAtlas atlas, Dictionary<exAtlas, List<exSpriteAnimClip>> byAtlas)
        {
            var anims = new List<object>();
            List<exSpriteAnimClip> clips;
            if (!byAtlas.TryGetValue(atlas, out clips)) return anims;
            var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach (var c in clips)
            {
                if (!seen.Add(c.name)) continue;
                var frames = new List<object>();
                var durations = new List<object>();
                foreach (var f in c.frameInfos) { frames.Add(f.index); durations.Add(f.length); }
                anims.Add(new Dictionary<string, object> { { "name", c.name }, { "frames", frames }, { "durations", durations } });
            }
            return anims;
        }

        static Dictionary<string, object> ClipJson(exSpriteAnimClip c)
        {
            var frames = new List<object>();
            var starts = new List<float>();
            float t = 0f;
            foreach (var f in c.frameInfos)
            {
                frames.Add(new Dictionary<string, object> { { "atlas", f.atlas != null ? f.atlas.name : null }, { "index", f.index }, { "length", f.length } });
                starts.Add(t);
                t += f.length;
            }
            var events = new List<object>();
            if (c.eventInfos != null)
                foreach (var e in c.eventInfos)
                {
                    int frame = 0;
                    while (frame + 1 < starts.Count && starts[frame + 1] <= e.time + 0.0001f) frame++;
                    var ev = new Dictionary<string, object> { { "time", e.time }, { "frame", frame }, { "method", e.methodName }, { "paramType", e.paramType } };
                    switch (e.paramType)
                    {
                        case exSpriteAnimClip.EventInfo.ParamType.INT: ev["param"] = e.intParam; break;
                        case exSpriteAnimClip.EventInfo.ParamType.FLOAT: ev["param"] = e.floatParam; break;
                        case exSpriteAnimClip.EventInfo.ParamType.STRING: ev["param"] = e.stringParam; break;
                        case exSpriteAnimClip.EventInfo.ParamType.BOOL: ev["param"] = e.boolParam; break;
                        case exSpriteAnimClip.EventInfo.ParamType.OBJECT: ev["param"] = e.objectParam != null ? e.objectParam.name : null; break;
                    }
                    events.Add(ev);
                }
            return new Dictionary<string, object>
            {
                { "name", c.name }, { "wrapMode", c.wrapMode }, { "speed", c.speed }, { "length", c.length },
                { "frames", frames }, { "events", events },
            };
        }

        static string FileName(string name)
        {
            var sb = new StringBuilder(string.IsNullOrEmpty(name) ? "unnamed" : name);
            foreach (var c in Path.GetInvalidFileNameChars()) sb.Replace(c, '_');
            return sb.ToString();
        }
    }
}
