using System;
using System.Collections.Generic;
using System.IO;
using BepInEx;
using BepInEx.Configuration;
using UnityEngine;

namespace CrawlFurther.Content.Ghosts
{
    using CrawlFurther.Art;
    using CrawlFurther.Gods;

    /// <summary>
    /// The silver and gold ghost slots' custom look: four parts (SHAPE, COLOUR, EYES, TRAIL), each a list of named choices
    /// drawn by tools/sprites/ghost_custom.py, picked per player and per slot, saved per player slot in
    /// BepInEx/config/CrawlFurther.GhostLooks.cfg.
    ///
    /// The look is composed at run time from three drawn part sheets, exactly like ghost_custom.compose():
    /// CustomGhostBody (the shape, drawn in key colours, with an eye anchor and a tail anchor marker per frame),
    /// CustomGhostTrails (stamped behind the body on the tail anchor) and CustomGhostEyes (stamped on the eye anchor);
    /// then the chosen COLOUR replaces the key colours. The result is a 22-frame sheet (Spawn 10, Idle 6, Run 6) in the
    /// vanilla ghost's 54 x 50 cell, cached per look, used for the in-game ghost (GhostPack.BodyFor), the editor preview
    /// and the picker portrait (the Idle frames framed in CustomGhostFrames' silver / gold frame).
    ///
    /// Editor API: PartCount / PartLabel / ChoiceCount / ChoiceName, Get / Set / Cycle, Summary,
    /// MechanicTitle / MechanicText, PreviewClip (29 x 24 framed portrait loop), BodyClip (full-size anim loop).
    /// </summary>
    public static partial class GhostCustom
    {
        public const int Shape = 0, Colour = 1, Eyes = 2, Trail = 3;
        public static readonly string[] PartLabels = { "SHAPE", "COLOUR", "EYES", "TRAIL" };
        public static int PartCount { get { return PartLabels.Length; } }
        public static string PartLabel(int part) { return part >= 0 && part < PartCount ? PartLabels[part] : ""; }

        static string[,] Table(int part)
        {
            switch (part)
            {
                case Shape: return ShapeTable;
                case Colour: return ColourNames;
                case Eyes: return EyesTable;
                default: return TrailTable;
            }
        }

        public static int ChoiceCount(int part) { return part >= 0 && part < PartCount ? Table(part).GetLength(0) : 0; }
        /// <summary>The choice's name as the editor shows it ("HOODED", "FROST", ...).</summary>
        public static string ChoiceName(int part, int i)
        {
            int n = ChoiceCount(part);
            return n == 0 ? "" : Table(part)[((i % n) + n) % n, 1];
        }

        // ------------------------------------------------------------------ per-player choices
        const int Players = 4;
        static readonly int[,,] s_look = new int[Players, 3, 4];   // [player, tier, part]
        static ConfigFile s_cfg;
        static readonly ConfigEntry<string>[,] s_entries = new ConfigEntry<string>[Players, 3];

        static int[] Defaults(SlotTier tier) { return tier == SlotTier.Gold ? DefaultGold : DefaultSilver; }

        public static int Get(int playerId, SlotTier tier, int part)
        {
            if (tier == SlotTier.Normal) tier = SlotTier.Silver;
            if (playerId < 0 || playerId >= Players || part < 0 || part >= PartCount) return 0;
            return s_look[playerId, (int)tier, part];
        }

        public static int[] Look(int playerId, SlotTier tier)
        {
            var l = new int[PartCount];
            for (int p = 0; p < PartCount; p++) l[p] = Get(playerId, tier, p);
            return l;
        }

        /// <summary>Choose (wraps round) and save straight away.</summary>
        public static void Set(int playerId, SlotTier tier, int part, int choice)
        {
            if (tier == SlotTier.Normal) tier = SlotTier.Silver;
            if (playerId < 0 || playerId >= Players || part < 0 || part >= PartCount) return;
            int n = ChoiceCount(part);
            s_look[playerId, (int)tier, part] = ((choice % n) + n) % n;
            Save(playerId, tier);
            try { Prune(); } catch (Exception e) { Plugin.Log.LogError("Ghost looks prune: " + e); }
        }

        public static void Cycle(int playerId, SlotTier tier, int part, int dir) { Set(playerId, tier, part, Get(playerId, tier, part) + dir); }

        /// <summary>"HOODED, FROST, STARS EYES, MIST TRAIL"</summary>
        public static string Summary(int playerId, SlotTier tier)
        {
            var l = Look(playerId, tier);
            string trail = ChoiceName(Trail, l[Trail]);
            return ChoiceName(Shape, l[Shape]) + ", " + ChoiceName(Colour, l[Colour]) + ", " + ChoiceName(Eyes, l[Eyes]) + " EYES, "
                   + (trail == "NONE" ? "NO TRAIL" : trail + " TRAIL");
        }

        public static string MechanicTitle(SlotTier tier) { return tier == SlotTier.Gold ? "THRALLS" : "ASCENSION"; }

        /// <summary>Plain words for the editor / picker panel (each line fits a panel). "ghost button" is left bare: the
        /// panels add the player's own button through GhostControls.Personalise.</summary>
        public static string MechanicText(SlotTier tier)
        {
            if (tier == SlotTier.Gold)
                return "As a monster, press the ghost button to jump out.\nThe body fights on as your gold thrall, one at a time";
            return "Your monsters drop silver orbs. Bank eight and your\nnext body is upgraded a tier (a final ascends)";
        }

        public static void Load()
        {
            try
            {
                if (s_cfg == null) s_cfg = new ConfigFile(Path.Combine(Paths.ConfigPath, "CrawlFurther.GhostLooks.cfg"), true);
                for (int pid = 0; pid < Players; pid++)
                    for (int t = 1; t <= 2; t++)
                    {
                        var tier = (SlotTier)t;
                        var e = s_cfg.Bind("Player" + (pid + 1), tier.ToString(), LookString(Defaults(tier)),
                                           "Custom " + tier.ToString().ToLowerInvariant() + " ghost: shape, colour, eyes, trail");
                        s_entries[pid, t] = e;
                        Parse(pid, tier, e.Value);
                    }
            }
            catch (Exception ex)
            {
                Plugin.Log.LogError("Ghost looks config: " + ex);
                for (int pid = 0; pid < Players; pid++)
                    for (int t = 1; t <= 2; t++) for (int p = 0; p < 4; p++) s_look[pid, t, p] = Defaults((SlotTier)t)[p];
            }
        }

        static string LookString(int[] l)
        {
            return ShapeTable[l[0], 0] + "," + ColourNames[l[1], 0] + "," + EyesTable[l[2], 0] + "," + TrailTable[l[3], 0];
        }

        static void Parse(int pid, SlotTier tier, string v)
        {
            var d = Defaults(tier);
            var parts = (v ?? "").Split(',');
            for (int p = 0; p < 4; p++)
            {
                int idx = d[p];
                if (p < parts.Length)
                {
                    var tb = Table(p);
                    for (int i = 0; i < tb.GetLength(0); i++)
                        if (string.Equals(tb[i, 0], parts[p].Trim(), StringComparison.OrdinalIgnoreCase)) { idx = i; break; }
                }
                s_look[pid, (int)tier, p] = idx;
            }
        }

        static void Save(int pid, SlotTier tier)
        {
            try
            {
                if (s_cfg == null) Load();
                var e = s_entries[pid, (int)tier];
                if (e != null) e.Value = LookString(Look(pid, tier));   // SaveOnConfigSet writes the file
            }
            catch (Exception ex) { Plugin.Log.LogError("Ghost looks save: " + ex); }
        }

        // ------------------------------------------------------------------ composition
        static readonly Dictionary<string, SpriteSheet> s_bodies = new Dictionary<string, SpriteSheet>();
        static readonly Dictionary<string, SpriteSheet> s_portraits = new Dictionary<string, SpriteSheet>();
        static readonly Dictionary<string, exSpriteAnimClip> s_clips = new Dictionary<string, exSpriteAnimClip>();
        static readonly Dictionary<string, Color32[]> s_pixels = new Dictionary<string, Color32[]>();
        const int CW = 54, CH = 50;

        static string Key(int[] l) { return l[0] + "-" + l[1] + "-" + l[2] + "-" + l[3]; }

        static Color32[] Pixels(SpriteSheet sh)
        {
            Color32[] px;
            if (s_pixels.TryGetValue(sh.id, out px)) return px;
            var tex = sh.atlas.texture as Texture2D;
            px = tex != null ? tex.GetPixels32() : null;
            s_pixels[sh.id] = px;
            return px;
        }

        /// <summary>The pixel (x, y) (y down) of cell <paramref name="frame"/> of a sheet.</summary>
        static Color32 At(SpriteSheet sh, Color32[] px, int frame, int x, int y)
        {
            var m = sh.manifest;
            if (x < 0 || y < 0 || x >= m.cellW || y >= m.cellH) return new Color32(0, 0, 0, 0);
            var tex = sh.atlas.texture;
            int W = tex.width, H = tex.height;
            int ix = (frame % m.cols) * m.cellW + x, iy = (frame / m.cols) * m.cellH + y;
            return px[(H - 1 - iy) * W + ix];
        }

        static bool Mark(Color32 c, int r) { return c.a > 0 && c.r == r && c.g == 0 && c.b == 0; }

        static Color32 Hex(int v, byte a) { return new Color32((byte)((v >> 16) & 255), (byte)((v >> 8) & 255), (byte)(v & 255), a); }

        static Color32 Recolor(Color32 c, int col)
        {
            if (c.a == 0 || c.g != 0 || c.b < 1 || c.b > 4) return c;
            if (c.r == 10) return Hex(ColourTable[col, c.b - 1], c.a);
            if (c.r == 11) return Hex(ColourTable[col, 4 + c.b - 1], c.a);
            if (c.r == 12 && c.b <= 3) return Hex(ColourTable[col, 8 + c.b - 1], c.a);
            return c;
        }

        /// <summary>One composed 54 x 50 frame (row-major, y down).</summary>
        static Color32[] ComposeFrame(SpriteSheet body, Color32[] bpx, int bframe, SpriteSheet eyes, Color32[] epx, SheetAnim ea,
                                      SpriteSheet trails, Color32[] tpx, SheetAnim ta, int k, int col)
        {
            var b = new Color32[CW * CH];
            int ex = -1, ey = -1, tx = -1, ty = -1;
            for (int y = 0; y < CH; y++)
                for (int x = 0; x < CW; x++)
                {
                    var c = At(body, bpx, bframe, x, y);
                    if (Mark(c, 14)) { ex = x; ey = y; }
                    else if (Mark(c, 15)) { tx = x; ty = y; }
                    b[y * CW + x] = c;
                }
            // a marker takes the colour of the pixel to its left
            foreach (var m in new[] { new Vector2(ex, ey), new Vector2(tx, ty) })
            {
                int mx = (int)m.x, my = (int)m.y;
                if (mx < 0) continue;
                var left = mx > 0 ? b[my * CW + mx - 1] : new Color32(0, 0, 0, 0);
                b[my * CW + mx] = (Mark(left, 14) || Mark(left, 15)) ? new Color32(0, 0, 0, 0) : left;
            }
            var o = new Color32[CW * CH];
            // trail behind (origin (18, 12) of a 30 x 28 cell = the tail anchor)
            if (tx >= 0 && ta != null && ta.frames.Length > 0)
            {
                int tf = ta.frames[k % ta.frames.Length];
                var tm = trails.manifest;
                for (int y = 0; y < tm.cellH; y++)
                    for (int x = 0; x < tm.cellW; x++)
                    {
                        var c = At(trails, tpx, tf, x, y);
                        if (c.a == 0) continue;
                        int X = tx + x - 18, Y = ty + y - 12;
                        if (X >= 0 && Y >= 0 && X < CW && Y < CH) o[Y * CW + X] = c;
                    }
            }
            for (int i = 0; i < o.Length; i++) if (b[i].a > 0) o[i] = b[i];
            // eyes on top (origin (5, 3) of an 11 x 7 cell = the eye anchor)
            if (ex >= 0 && ea != null && ea.frames.Length > 0)
            {
                int ef = ea.frames[k % ea.frames.Length];
                var em = eyes.manifest;
                for (int y = 0; y < em.cellH; y++)
                    for (int x = 0; x < em.cellW; x++)
                    {
                        var c = At(eyes, epx, ef, x, y);
                        if (c.a == 0) continue;
                        int X = ex + x - 5, Y = ey + y - 3;
                        if (X >= 0 && Y >= 0 && X < CW && Y < CH) o[Y * CW + X] = c;
                    }
            }
            for (int i = 0; i < o.Length; i++) o[i] = Recolor(o[i], col);
            return o;
        }

        /// <summary>Pack frames (row-major, y down, w x h each) into a point-filtered POT texture + a SpriteSheet.</summary>
        static SpriteSheet Pack(string id, List<Color32[]> frames, int w, int h, int cols, SheetAnim[] anims)
        {
            int rows = (frames.Count + cols - 1) / cols;
            int W = 1, H = 1;
            while (W < cols * w) W *= 2;
            while (H < rows * h) H *= 2;
            var px = new Color32[W * H];
            for (int f = 0; f < frames.Count; f++)
            {
                int x0 = (f % cols) * w, y0 = (f / cols) * h;
                for (int y = 0; y < h; y++)
                    for (int x = 0; x < w; x++)
                        px[(H - 1 - (y0 + y)) * W + x0 + x] = frames[f][y * w + x];
            }
            var tex = new Texture2D(W, H, TextureFormat.ARGB32, false) { filterMode = FilterMode.Point, wrapMode = TextureWrapMode.Clamp, name = id };
            tex.SetPixels32(px);
            tex.Apply(false);
            tex.hideFlags |= HideFlags.DontUnloadUnusedAsset;
            var elems = new exAtlas.Element[frames.Count];
            for (int i = 0; i < frames.Count; i++)
            {
                int x = (i % cols) * w, yTop = (i / cols) * h;
                elems[i] = new exAtlas.Element
                {
                    name = id + "_" + i, originalWidth = w, originalHeight = h, trimRect = new Rect(0, 0, w, h),
                    coords = new Rect((float)x / W, (float)(H - yTop - h) / H, (float)w / W, (float)h / H), rotated = false
                };
            }
            var atlas = ScriptableObject.CreateInstance<exAtlas>();
            atlas.name = "ModAtlas_" + id;
            atlas.texture = tex;
            atlas.elements = elems;
            var mat = new Material(SpriteSheets.TemplateMaterial) { name = "ModMat_" + id, mainTexture = tex };
            atlas.material = mat;
            atlas.hideFlags |= HideFlags.DontUnloadUnusedAsset;
            mat.hideFlags |= HideFlags.DontUnloadUnusedAsset;
            return new SpriteSheet(id, atlas, new SheetManifest { cellW = w, cellH = h, cols = cols, anims = anims });
        }

        static SpriteSheet ComposeBody(int[] l)
        {
            string key = Key(l);
            SpriteSheet s;
            if (s_bodies.TryGetValue(key, out s) && s != null) return s;
            var body = SpriteSheets.Get("CustomGhostBody"); var eyes = SpriteSheets.Get("CustomGhostEyes"); var trails = SpriteSheets.Get("CustomGhostTrails");
            if (body == null || eyes == null || trails == null) return null;
            var bpx = Pixels(body); var epx = Pixels(eyes); var tpx = Pixels(trails);
            if (bpx == null || epx == null || tpx == null) return null;
            string shape = ShapeTable[l[Shape], 0];
            var ea = eyes.Anim(EyesTable[l[Eyes], 0]);
            var ta = trails.Anim(TrailTable[l[Trail], 0]);
            var frames = new List<Color32[]>();
            var anims = new List<SheetAnim>();
            foreach (var an in new[] { "Spawn", "Idle", "Run" })
            {
                var a = body.Anim(shape + an);
                if (a == null) return null;
                var idx = new int[a.frames.Length];
                for (int k = 0; k < a.frames.Length; k++)
                {
                    idx[k] = frames.Count;
                    frames.Add(ComposeFrame(body, bpx, a.frames[k], eyes, epx, ea, trails, tpx, ta, k, l[Colour]));
                }
                anims.Add(new SheetAnim { name = an, frames = idx, durations = a.durations });
            }
            s = Pack("GhostLook_" + key, frames, CW, CH, 8, anims.ToArray());
            s_bodies[key] = s;
            Plugin.Log.LogInfo("Ghost look composed: " + Summary(l));
            return s;
        }

        static string Summary(int[] l)
        {
            return ChoiceName(Shape, l[0]) + " " + ChoiceName(Colour, l[1]) + " " + ChoiceName(Eyes, l[2]) + " " + ChoiceName(Trail, l[3]);
        }

        /// <summary>The framed 29 x 24 portrait: only the four Idle frames it shows are composed (straight from the part
        /// sheets, no full body sheet), so stepping through looks in the editor costs one 128 x 32 texture each.</summary>
        static SpriteSheet ComposePortrait(SlotTier tier, int[] l)
        {
            string key = tier + "_" + Key(l);
            SpriteSheet s;
            if (s_portraits.TryGetValue(key, out s) && s != null) return s;
            var body = SpriteSheets.Get("CustomGhostBody"); var eyes = SpriteSheets.Get("CustomGhostEyes");
            var trails = SpriteSheets.Get("CustomGhostTrails"); var frm = SpriteSheets.Get("CustomGhostFrames");
            if (body == null || eyes == null || trails == null || frm == null) return null;
            var bpx = Pixels(body); var epx = Pixels(eyes); var tpx = Pixels(trails); var fpx = Pixels(frm);
            var fa = frm.Anim(tier == SlotTier.Gold ? "Gold" : "Silver");
            var idle = body.Anim(ShapeTable[l[Shape], 0] + "Idle");
            var ea = eyes.Anim(EyesTable[l[Eyes], 0]);
            var ta = trails.Anim(TrailTable[l[Trail], 0]);
            if (bpx == null || epx == null || tpx == null || fpx == null || fa == null || idle == null) return null;
            int wx = WinX[l[Shape]], wy = WinY[l[Shape]];
            var frames = new List<Color32[]>();
            for (int i = 0; i < 4; i++)
            {
                int k = Mathf.Min(idle.frames.Length - 1, (i * 3) / 2);
                var look = ComposeFrame(body, bpx, idle.frames[k], eyes, epx, ea, trails, tpx, ta, k, l[Colour]);
                var o = new Color32[29 * 24];
                for (int y = 0; y < 24; y++)
                    for (int x = 0; x < 29; x++)
                    {
                        var bg = At(frm, fpx, fa.frames[i % fa.frames.Length], x, y);
                        bool border = x < 2 || x > 26 || y < 2 || y > 21;
                        int X = wx + x, Y = wy + y;
                        var c = border || X < 0 || Y < 0 || X >= CW || Y >= CH ? new Color32(0, 0, 0, 0) : look[Y * CW + X];
                        float a = c.a / 255f;
                        o[y * 29 + x] = new Color32((byte)(c.r * a + bg.r * (1 - a)), (byte)(c.g * a + bg.g * (1 - a)), (byte)(c.b * a + bg.b * (1 - a)), 255);
                    }
                frames.Add(o);
            }
            s = Pack("GhostLookPortrait_" + key, frames, 29, 24, 4,
                     new[] { new SheetAnim { name = "Idle", frames = new[] { 0, 1, 2, 3 }, durations = new[] { 0.25f, 0.2f, 0.25f, 0.2f } } });
            CrawlFurther.UI.ModMark.MarkArt(s.atlas);   // mod art: the menus give it the one violet gem
            s_portraits[key] = s;
            return s;
        }

        /// <summary>The look each (player, tier) was last handed out for display: still on screen until the next clip
        /// replaces it, so Prune never destroys it (the editor calls Set, then asks for the new clip).</summary>
        static readonly Dictionary<int, string> s_shownPortrait = new Dictionary<int, string>();
        static readonly Dictionary<int, string> s_shownBody = new Dictionary<int, string>();

        /// <summary>
        /// Keep composed bodies and portraits only for the looks players have stored or are being shown (4 players x silver / gold); destroy
        /// the textures, materials, atlases, clips and ghost prefabs of any other look (editor steps, self test).
        /// </summary>
        static void Prune()
        {
            var keepBody = new HashSet<string>(s_shownBody.Values);
            var keepPortrait = new HashSet<string>(s_shownPortrait.Values);
            for (int pid = 0; pid < Players; pid++)
                for (int t = 1; t <= 2; t++)
                {
                    string k = Key(Look(pid, (SlotTier)t));
                    keepBody.Add(k);
                    keepPortrait.Add((SlotTier)t + "_" + k);
                }
            Drop(s_bodies, keepBody, true);
            Drop(s_portraits, keepPortrait, false);
        }

        static void Drop(Dictionary<string, SpriteSheet> cache, HashSet<string> keep, bool body)
        {
            var gone = new List<string>();
            foreach (var kv in cache) if (!keep.Contains(kv.Key)) gone.Add(kv.Key);
            if (gone.Count == 0) return;
            var used = AtlasesInUse();
            foreach (var k in gone)
            {
                var sh = cache[k];
                // anything still drawing or animating with this look (an in-game ghost, a picker or vault portrait, an
                // editor preview) keeps it: it is tried again on the next prune
                if (sh != null && sh.atlas != null && used.Contains(sh.atlas)) continue;
                cache.Remove(k);
                if (sh == null) continue;
                // the ghost prefabs built on it are only forgotten (pooled instances may still point at them, but nothing
                // spawns a forgotten prefab again). Clips are kept from unloading (SpriteSheets.Keep), so they are destroyed
                // here with the texture: nothing active is drawing this atlas (checked above), and the menus that may
                // still list one (SafePlay / CheckPortrait) skip destroyed clips
                var dead = body ? GhostPack.ForgetLook(sh.id) : new List<exSpriteAnimClip>();
                var clipKeys = new List<string>();
                foreach (var ck in s_clips.Keys) if (ck.Contains(sh.id) || (!body && ck == "P_" + k)) clipKeys.Add(ck);
                foreach (var ck in clipKeys)
                {
                    var c = s_clips[ck];
                    if (c != null && !dead.Contains(c)) dead.Add(c);
                    s_clips.Remove(ck);
                }
                foreach (var c in dead) if (c != null) UnityEngine.Object.Destroy(c);
                s_pixels.Remove(sh.id);
                if (sh.atlas != null)
                {
                    if (sh.atlas.texture != null) UnityEngine.Object.Destroy(sh.atlas.texture);
                    if (sh.atlas.material != null) UnityEngine.Object.Destroy(sh.atlas.material);
                    UnityEngine.Object.Destroy(sh.atlas);
                }
            }
        }

        /// <summary>Every atlas an active sprite shows or an active sprite animation is playing right now.</summary>
        static HashSet<exAtlas> AtlasesInUse()
        {
            var set = new HashSet<exAtlas>();
            foreach (var spr in UnityEngine.Object.FindObjectsOfType<exSprite>())
                if (spr != null && spr.atlas != null) set.Add(spr.atlas);
            foreach (var sa in UnityEngine.Object.FindObjectsOfType<exSpriteAnimation>())
            {
                if (sa == null) continue;
                var st = sa.GetCurrentAnimation();
                if (st != null && st.clip != null && st.clip.frameInfos != null && st.clip.frameInfos.Count > 0 && st.clip.frameInfos[0].atlas != null)
                    set.Add(st.clip.frameInfos[0].atlas);
            }
            return set;
        }

        /// <summary>The composed in-game body of a player's custom ghost (Spawn / Idle / Run), or null.</summary>
        public static SpriteSheet BodySheet(int playerId, SlotTier tier)
        {
            try { return ComposeBody(Look(playerId, tier)); }
            catch (Exception e) { Plugin.Log.LogError("Ghost look compose failed: " + e); return null; }
        }

        /// <summary>The picker portrait of a custom slot: the player's look in the silver / gold frame (29 x 24 loop).</summary>
        public static exSpriteAnimClip PortraitClip(int playerId, SlotTier tier)
        {
            if (tier == SlotTier.Normal) return null;
            try
            {
                var l = Look(playerId, tier);
                s_shownPortrait[playerId * 3 + (int)tier] = tier + "_" + Key(l);
                string key = "P_" + tier + "_" + Key(l);
                exSpriteAnimClip c;
                if (s_clips.TryGetValue(key, out c) && c != null) return c;
                var s = ComposePortrait(tier, l);
                if (s == null) return null;
                c = new ClipBuilder(s, "Idle", "ModGhostLookPortrait_" + key).Loop().Build();
                s_clips[key] = c;
                return c;
            }
            catch (Exception e) { Plugin.Log.LogError("Ghost look portrait failed: " + e); return null; }
        }

        /// <summary>The editor's live preview: the portrait-sized framed look of the slot the player has highlighted
        /// (silver unless their highlighted ghost entry is the gold one).</summary>
        public static exSpriteAnimClip PreviewClip(int playerId)
        {
            int i;
            var tier = SlotTier.Silver;
            if (GhostPack.Chosen.TryGetValue(playerId, out i) && i >= 0 && i < GhostPack.Forms.Count && GhostPack.Forms[i].tier == SlotTier.Gold)
                tier = SlotTier.Gold;
            return PortraitClip(playerId, tier);
        }

        public static exSpriteAnimClip PreviewClip(int playerId, SlotTier tier) { return PortraitClip(playerId, tier); }

        /// <summary>The full-size (54 x 50 cell) composed anim, looping: "Idle", "Run" or "Spawn".</summary>
        public static exSpriteAnimClip BodyClip(int playerId, SlotTier tier, string anim = "Idle")
        {
            var s = BodySheet(playerId, tier);
            if (s == null || !s.Has(anim)) return null;
            s_shownBody[playerId * 3 + (int)tier] = Key(Look(playerId, tier));
            string key = "B_" + s.id + "_" + anim;
            exSpriteAnimClip c;
            if (s_clips.TryGetValue(key, out c) && c != null) return c;
            c = new ClipBuilder(s, anim, "ModGhostLook_" + key).Loop().Build();
            s_clips[key] = c;
            return c;
        }

        // ------------------------------------------------------------------ self test
        public static void SelfCheck(Action<string> bad)
        {
            var body = SpriteSheets.Get("CustomGhostBody");
            if (body == null) { bad("CustomGhostBody art missing"); return; }
            for (int s = 0; s < ShapeTable.GetLength(0); s++)
                foreach (var an in new[] { "Spawn", "Idle", "Run" })
                    if (!body.Has(ShapeTable[s, 0] + an)) bad("CustomGhostBody has no " + ShapeTable[s, 0] + an);
            var eyes = SpriteSheets.Get("CustomGhostEyes"); var trails = SpriteSheets.Get("CustomGhostTrails");
            if (eyes == null || trails == null) { bad("CustomGhostEyes / CustomGhostTrails art missing"); return; }
            for (int i = 0; i < EyesTable.GetLength(0); i++) if (!eyes.Has(EyesTable[i, 0])) bad("CustomGhostEyes has no " + EyesTable[i, 0]);
            for (int i = 0; i < TrailTable.GetLength(0); i++) if (!trails.Has(TrailTable[i, 0])) bad("CustomGhostTrails has no " + TrailTable[i, 0]);
            if (SpriteSheets.Get("CustomGhostFrames") == null) bad("CustomGhostFrames art missing");
            // compose every shape once with every colour index range and the defaults (catches unreadable textures)
            var bpx = Pixels(body); var epx = Pixels(eyes); var tpx = Pixels(trails);
            if (bpx == null || epx == null || tpx == null) { bad("custom ghost part textures are not readable"); return; }
            for (int s = 0; s < ShapeTable.GetLength(0); s++)
            {
                var a = body.Anim(ShapeTable[s, 0] + "Idle");
                if (a == null) continue;
                var f = ComposeFrame(body, bpx, a.frames[0], eyes, epx, eyes.Anim(EyesTable[s % EyesTable.GetLength(0), 0]),
                                     trails, tpx, trails.Anim(TrailTable[(s + 1) % TrailTable.GetLength(0), 0]), 0, s % ColourTable.GetLength(0));
                int n = 0;
                foreach (var c in f) if (c.a > 0) { n++; if (c.g == 0 && c.b >= 1 && c.b <= 4 && c.r >= 10 && c.r <= 15) { bad("custom ghost shape " + ShapeTable[s, 0] + " left a key colour"); break; } }
                if (n < 40) bad("custom ghost shape " + ShapeTable[s, 0] + " composed almost empty");
            }
            if (ComposePortrait(SlotTier.Gold, DefaultGold) == null || ComposePortrait(SlotTier.Silver, DefaultSilver) == null)
                bad("custom ghost portraits failed to compose");
            Prune();
            // every stored look's in-game body and picker portrait survive a prune (nothing on screen is destroyed)
            var bodies = new List<SpriteSheet>(); var portraits = new List<SpriteSheet>(); var clips = new List<exSpriteAnimClip>();
            for (int pid = 0; pid < Players; pid++)
                for (int t = 1; t <= 2; t++)
                {
                    var b = BodySheet(pid, (SlotTier)t);
                    var pc = PortraitClip(pid, (SlotTier)t);
                    if (pc != null) clips.Add(pc);
                    if (pc == null || b == null) { bad("custom ghost P" + (pid + 1) + " " + (SlotTier)t + " look failed to compose"); continue; }
                    bodies.Add(b);
                    SpriteSheet ps; if (s_portraits.TryGetValue((SlotTier)t + "_" + Key(Look(pid, (SlotTier)t)), out ps)) portraits.Add(ps);
                }
            ComposePortrait(SlotTier.Silver, new[] { 5, 2, 4, 2 });   // a look nobody stored: the prune may drop it
            Prune();
            // (Destroy only happens at the end of the frame, so check the caches: a dropped look leaves them)
            foreach (var sh in bodies) if (!s_bodies.ContainsValue(sh) || sh.atlas == null || sh.atlas.texture == null) bad("prune dropped a stored ghost body " + sh.id);
            foreach (var sh in portraits) if (!s_portraits.ContainsValue(sh) || sh.atlas == null || sh.atlas.texture == null) bad("prune dropped a stored ghost portrait " + sh.id);
            foreach (var c in clips) if (!s_clips.ContainsValue(c)) bad("prune freed a stored ghost portrait clip " + c.name);
        }
    }
}
