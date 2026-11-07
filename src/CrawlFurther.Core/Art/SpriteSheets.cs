using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

namespace CrawlFurther.Art
{
    /// <summary>
    /// Loads sprite sheets (Name.png + Name.json, see <see cref="SheetManifest"/>) from the art folders of every mod
    /// built on Core, and keeps runtime-made art alive for the whole session.
    /// </summary>
    public static class SpriteSheets
    {
        static readonly List<string> s_folders = new List<string>();
        static readonly Dictionary<string, SpriteSheet> s_sheets = new Dictionary<string, SpriteSheet>();
        // ByAtlas runs every frame for the menu badge: a lookup, not a scan of every sheet
        static readonly Dictionary<exAtlas, SpriteSheet> s_byAtlas = new Dictionary<exAtlas, SpriteSheet>();
        static Material s_templateMaterial;

        /// <summary>
        /// Add <paramref name="modDir"/>/art to the folders <see cref="Get"/> searches. Core adds the folder of every mod
        /// registered with <see cref="Further.AddMod"/>; call this only for art kept somewhere else. Folders are searched
        /// in the order they were added; adding one twice does nothing.
        /// </summary>
        public static void AddFolder(string modDir)
        {
            if (string.IsNullOrEmpty(modDir)) return;
            var dir = Path.GetFullPath(Path.Combine(modDir, "art"));
            foreach (var f in s_folders) if (string.Equals(f, dir, StringComparison.OrdinalIgnoreCase)) return;
            s_folders.Add(dir);
        }

        /// <summary>
        /// The path of <paramref name="file"/> (e.g. "MyMonster.png") in the first art folder that has it, or in the first
        /// folder when none does, so a "missing" message names a real place.
        /// </summary>
        public static string PathOf(string file)
        {
            foreach (var d in s_folders)
            {
                var p = Path.Combine(d, file);
                if (File.Exists(p)) return p;
            }
            return Path.Combine(s_folders.Count > 0 ? s_folders[0] : Path.Combine(FurtherCore.ModDir ?? "", "art"), file);
        }

        /// <summary>
        /// The sheet <paramref name="id"/>, loaded from the first art folder that has id.png and id.json, or null (with a
        /// warning in the log) when it is missing. Loaded once; later calls return the same sheet.
        /// </summary>
        public static SpriteSheet Get(string id)
        {
            SpriteSheet s;
            if (s_sheets.TryGetValue(id, out s)) return s;
            var png = PathOf(id + ".png");
            return Remember(id, LoadFile(id, png, Path.Combine(Path.GetDirectoryName(png), id + ".json")));
        }

        /// <summary>
        /// The sheet <paramref name="id"/> from <paramref name="modDir"/>/art exactly, ignoring the other folders. Use it
        /// when another mod may ship a sheet with the same id. Loaded once, like <see cref="Get"/>.
        /// </summary>
        public static SpriteSheet Load(string modDir, string id)
        {
            SpriteSheet s;
            if (s_sheets.TryGetValue(id, out s)) return s;
            var dir = Path.Combine(modDir, "art");
            return Remember(id, LoadFile(id, Path.Combine(dir, id + ".png"), Path.Combine(dir, id + ".json")));
        }

        static SpriteSheet Remember(string id, SpriteSheet s)
        {
            s_sheets[id] = s;
            if (s != null && s.atlas != null) s_byAtlas[s.atlas] = s;
            return s;
        }

        /// <summary>The sheet an atlas came from, or null for vanilla atlases and sheets not loaded through this class.</summary>
        public static SpriteSheet ByAtlas(exAtlas a)
        {
            if (a == null) return null;
            SpriteSheet s;
            return s_byAtlas.TryGetValue(a, out s) ? s : null;
        }

        static SpriteSheet LoadFile(string id, string png, string json)
        {
            if (!File.Exists(png) || !File.Exists(json))
            {
                FurtherCore.Log.LogWarning("Art missing for " + id + " (" + png + ")");
                return null;
            }
            var tex = new Texture2D(2, 2, TextureFormat.ARGB32, false);
            tex.LoadImage(File.ReadAllBytes(png));
            tex.filterMode = FilterMode.Point;
            tex.wrapMode = TextureWrapMode.Clamp;
            tex.name = "Mod_" + id;
            var m = SheetManifest.Parse(File.ReadAllText(json));
            var sheet = FromTexture(id, tex, m);
            FurtherCore.Log.LogInfo(string.Format("Loaded art {0}: {1}x{2}, {3} cells, {4} anims",
                id, tex.width, tex.height, sheet.atlas.elements.Length, m.anims == null ? 0 : m.anims.Length));
            return sheet;
        }

        /// <summary>
        /// Make a sheet from a texture already in memory (generated or recoloured art), laid out as <paramref name="manifest"/>
        /// says. The texture, atlas and material are kept for the session. The sheet is not cached, so <see cref="Get"/>
        /// and <see cref="ByAtlas"/> do not know it.
        /// </summary>
        public static SpriteSheet FromTexture(string id, Texture2D tex, SheetManifest manifest)
        {
            Keep(tex);
            int W = tex.width, H = tex.height;
            int cw = manifest.cellW, ch = manifest.cellH;
            int count = (W / cw) * (H / ch);
            var elems = new exAtlas.Element[count];
            for (int i = 0; i < count; i++)
            {
                int x = (i % manifest.cols) * cw, yTop = (i / manifest.cols) * ch;
                elems[i] = new exAtlas.Element
                {
                    name = id + "_" + i,
                    originalWidth = cw,
                    originalHeight = ch,
                    trimRect = new Rect(0, 0, cw, ch),
                    coords = new Rect((float)x / W, (float)(H - yTop - ch) / H, (float)cw / W, (float)ch / H),
                    rotated = false
                };
            }
            var atlas = ScriptableObject.CreateInstance<exAtlas>();
            atlas.name = "ModAtlas_" + id;
            atlas.texture = tex;
            atlas.elements = elems;
            var mat = new Material(TemplateMaterial);
            mat.name = "ModMat_" + id;
            mat.mainTexture = tex;
            atlas.material = mat;
            Keep(atlas);
            Keep(mat);
            return new SpriteSheet(id, atlas, manifest);
        }

        /// <summary>
        /// Keep a runtime-made object for the whole session. Assets (textures, atlases, materials, clips) get
        /// HideFlags.DontUnloadUnusedAsset: on Unity 5.4, DontDestroyOnLoad accepts only root GameObjects (or their
        /// components) and on anything else just logs an error, and scene loads drop assets only through
        /// UnloadUnusedAssets, which the flag exempts them from. Root GameObjects get DontDestroyOnLoad; a child lives
        /// and dies with its root.
        /// </summary>
        public static void Keep(UnityEngine.Object o)
        {
            if (o == null) return;
            var go = o as GameObject ?? (o is Component ? ((Component)o).gameObject : null);
            if (go != null)
            {
                if (go.transform.parent == null) UnityEngine.Object.DontDestroyOnLoad(go);
                return;
            }
            o.hideFlags |= HideFlags.DontUnloadUnusedAsset;
        }

        /// <summary>
        /// The material of the game's monster atlas (its paletted sprite shader). New atlases copy it so they take the
        /// game's colour swaps and flashes like vanilla art. Null until the game has loaded its monsters.
        /// </summary>
        public static Material TemplateMaterial
        {
            get
            {
                if (s_templateMaterial == null)
                {
                    foreach (var a in Resources.FindObjectsOfTypeAll<exAtlas>())
                        if (a.name == "AtlasEnemies") { s_templateMaterial = a.material; break; }
                }
                return s_templateMaterial;
            }
        }

        /// <summary>
        /// A clip for <paramref name="anim"/> of <paramref name="sheet"/> that copies <paramref name="template"/> (a vanilla
        /// clip, or null for a plain looping clip). With the same frame count and no durations in the manifest, the
        /// template's frame timings are kept, so its events (AnimAttack, AnimSound...) stay on the same frames; otherwise
        /// the events are stretched to the new length. Returns null when the sheet has no such animation.
        /// </summary>
        public static exSpriteAnimClip MakeClip(SpriteSheet sheet, string anim, exSpriteAnimClip template, string clipName)
        {
            var a = sheet == null ? null : sheet.Anim(anim);
            if (a == null) return null;
            exSpriteAnimClip c;
            if (template != null) c = UnityEngine.Object.Instantiate(template);
            else
            {
                c = ScriptableObject.CreateInstance<exSpriteAnimClip>();
                c.wrapMode = WrapMode.Loop;
            }
            c.name = clipName;
            float oldLen = 0f;
            if (template != null) foreach (var f in template.frameInfos) oldLen += f.length;

            bool keepTiming = template != null && template.frameInfos.Count == a.frames.Length && (a.durations == null || a.durations.Length == 0);
            var frames = new List<exSpriteAnimClip.FrameInfo>(a.frames.Length);
            float newLen = 0f;
            for (int i = 0; i < a.frames.Length; i++)
            {
                float len = keepTiming ? template.frameInfos[i].length
                    : (a.durations != null && i < a.durations.Length ? a.durations[i] : 0.1f);
                frames.Add(new exSpriteAnimClip.FrameInfo { atlas = sheet.atlas, index = a.frames[i], length = len, textureGUID = "" });
                newLen += len;
            }
            c.frameInfos = frames;
            if (template != null && oldLen > 0f && Mathf.Abs(newLen - oldLen) > 0.0005f && c.eventInfos != null)
            {
                float k = newLen / oldLen;
                foreach (var e in c.eventInfos) e.time *= k;
            }
            c.length = newLen;
            Keep(c);
            return c;
        }
    }
}
