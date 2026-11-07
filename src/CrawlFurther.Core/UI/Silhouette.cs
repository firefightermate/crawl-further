using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.UI
{
    using CrawlFurther.Art;
    using CrawlFurther.Compat;

    /// <summary>Silhouettes of sheet frames (the pictures of secrets not found yet).</summary>
    internal static class Silhouette
    {
        /// <summary>A one-frame clip of a sheet frame drawn as a silhouette: the same pixels in a dusky near-black with a
        /// faint violet rim, trimmed to the shape (like a vanilla atlas element) so the vault centres it.</summary>
        public static exSpriteAnimClip Clip(SpriteSheet sh, int frame, string name)
        {
            try
            {
                var src = sh.atlas.texture as Texture2D;
                var m = sh.manifest;
                int col = frame % m.cols, row = frame / m.cols;
                int x0 = col * m.cellW, y0 = src.height - (row + 1) * m.cellH;
                var px = src.GetPixels32(0);
                int W = m.cellW, H = m.cellH;
                var outp = new Color32[W * H];
                int minX = W, minY = H, maxX = -1, maxY = -1;
                Func<int, int, bool> ink = (x, y) => x >= 0 && y >= 0 && x < W && y < H && px[(y0 + y) * src.width + x0 + x].a > 0;
                for (int y = 0; y < H; y++)
                    for (int x = 0; x < W; x++)
                    {
                        if (!ink(x, y)) continue;
                        bool edge = !ink(x - 1, y) || !ink(x + 1, y) || !ink(x, y - 1) || !ink(x, y + 1);
                        outp[y * W + x] = edge ? new Color32(74, 58, 92, 255) : new Color32(26, 20, 32, 255);
                        if (x < minX) minX = x; if (x > maxX) maxX = x; if (y < minY) minY = y; if (y > maxY) maxY = y;
                    }
                if (maxX < 0) return null;
                var tex = new Texture2D(W, H, TextureFormat.ARGB32, false) { filterMode = FilterMode.Point, wrapMode = TextureWrapMode.Clamp, name = OnlineNames.ComposedTexture(sh.id, frame.ToString(), "silhouette") };
                tex.SetPixels32(outp);
                tex.Apply(false);
                SpriteSheets.Keep(tex);
                int bw = maxX - minX + 1, bh = maxY - minY + 1;
                var el = new exAtlas.Element
                {
                    name = name, originalWidth = W, originalHeight = H,
                    trimRect = new Rect(minX, H - 1 - maxY, bw, bh),
                    coords = new Rect((float)minX / W, (float)minY / H, (float)bw / W, (float)bh / H),
                    rotated = false,
                };
                var atlas = ScriptableObject.CreateInstance<exAtlas>();
                atlas.name = OnlineNames.Atlas(name);
                atlas.texture = tex;
                atlas.elements = new[] { el };
                var mat = new Material(SpriteSheets.TemplateMaterial) { name = OnlineNames.Material(name), mainTexture = tex };
                atlas.material = mat;
                SpriteSheets.Keep(atlas); SpriteSheets.Keep(mat);
                var c = ScriptableObject.CreateInstance<exSpriteAnimClip>();
                c.name = name;
                c.wrapMode = WrapMode.Loop;
                c.frameInfos = new List<exSpriteAnimClip.FrameInfo> { new exSpriteAnimClip.FrameInfo { atlas = atlas, index = 0, length = 1f, textureGUID = "" } };
                c.length = 1f;
                SpriteSheets.Keep(c);
                return c;
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Secret silhouette " + name + ": " + e.Message); return null; }
        }
    }
}
