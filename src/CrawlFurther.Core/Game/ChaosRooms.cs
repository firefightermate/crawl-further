using System;
using System.Collections.Generic;
using System.Text.RegularExpressions;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Game
{
    using CrawlFurther.Art;
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Crawl Chaos's big rooms: each of the game's own rooms, widened and deepened, still one screen (the camera frames a
    /// bigger room by zooming out, as it does for the boss arenas). In a chaos game most rooms on a floor are the big
    /// ones; a room that can't grow cleanly keeps its own size.
    /// <para>How a room grows, once per session, on a copy kept as a prefab:</para>
    /// <list type="bullet">
    /// <item>one seam down the floor and one across it, each where no door, prop or set piece crosses it, in the widest
    /// stretch of plain floor;</item>
    /// <item>everything past a seam moves out (doors, walls, set pieces, the room's outline and camera frame), and walls
    /// that cross a seam get longer;</item>
    /// <item>the gap is filled with strips of the room's own floor and back wall from near the seam. Each strip is the
    /// one whose edge best carries on from the strip before it, and only strips that look like the floor at the seam
    /// (no inset borders, symbols or water edges) are used, so the stone and mottling run on;</item>
    /// <item>small set dressing in a copied strip (bricks in the wall, column bases, stray boards) is copied with it.</item>
    /// </list>
    /// The new floor and wall images are built from the game's own art at runtime; nothing of the game's is shipped.
    /// <c>tools/chaos/room_stretch.py</c> draws the same result from the asset dump, to look at before playing.
    /// </summary>
    public static class ChaosRooms
    {
        /// <summary>Off: chaos floors use the game's own rooms.</summary>
        public static bool Enabled = true;
        /// <summary>A big room is picked this many times as often as the same room at its own size.</summary>
        public static float BigWeight = 4f;
        /// <summary>Spawners in a big room: the room's usual count times 1 + (area ratio - 1) times this.</summary>
        public static float EnemyGrowth = 0.5f;

        // limits shared with tools/chaos/room_stretch.py
        const float MaxW = 320f, MaxH = 160f, GrowW = 1.6f, GrowH = 1.35f;
        const float DoorClear = 10f, Edge = 14f, Alike = 14f, Near = 6f;
        const int Window = 56, MinBlock = 6, BlockMin = 22, BlockMax = 40, MinAlike = 28;
        const float SrcX0 = 0.25f, SrcX1 = 0.75f, SrcY0 = 0.3f, SrcY1 = 0.7f;

        static readonly Regex Strip = new Regex(@"^(BackWallArt\d*|ColumnArt|ColumnArtShadow|ColumnShadows?)$");
        static readonly Regex Copy = new Regex(@"^(BackWallBricks|ColumnCollision|Column|Columns|ColumnShadows?|FloorStrayBoards|Candle|PropWallFlag|Bookshelf|RockDebrisFloor)\d*$");
        static readonly Regex Skip = new Regex(@"^(Walls|WallsTop|RoomBounds|SpawnConstraint ?)$");
        static readonly Regex NotRoom = new Regex(@"HeroBattle|Powerup|Store|Portal|Boss|^Tute");

        static readonly Dictionary<GameObject, Room> s_big = new Dictionary<GameObject, Room>();
        static readonly Dictionary<SpawnGroup, SpawnGroup> s_groups = new Dictionary<SpawnGroup, SpawnGroup>();
        static readonly Dictionary<Texture, Texture2D> s_readable = new Dictionary<Texture, Texture2D>();
        static GameObject s_groupHolder;

        /// <summary>The chaos version of a room group: each room that can grow is there big (weighted <see cref="BigWeight"/>)
        /// and at its own size.</summary>
        public static SpawnGroup GroupFor(SpawnGroup orig)
        {
            if (orig == null || !Enabled) return orig;
            SpawnGroup g;
            if (s_groups.TryGetValue(orig, out g) && g != null) return g;
            try
            {
                if (s_groupHolder == null)
                {
                    s_groupHolder = new GameObject("CrawlMod_ChaosRoomGroups");
                    s_groupHolder.SetActive(false);
                    UnityEngine.Object.DontDestroyOnLoad(s_groupHolder);
                }
                var go = new GameObject("Chaos" + orig.name);
                go.transform.parent = s_groupHolder.transform;
                g = go.AddComponent<SpawnGroup>();
                g.m_items = new List<SpawnItem>();
                g.m_numToSpawn = orig.m_numToSpawn;
                int big = 0, all = 0;
                AddItems(orig, 1f, g.m_items, ref big, ref all);
                s_groups[orig] = g;
                FurtherCore.Log.LogInfo("Chaos: " + orig.name + " has " + big + " big rooms out of " + all);
                return g;
            }
            catch (Exception e)
            {
                FurtherCore.Log.LogError("Chaos rooms: " + orig.name + ": " + e);
                s_groups[orig] = orig;
                return orig;
            }
        }

        static void AddItems(SpawnGroup src, float scale, List<SpawnItem> into, ref int big, ref int all)
        {
            float total = 0f;
            foreach (var it in src.m_items) if (it != null && it.m_object != null) total += it.m_chance;
            if (total <= 0f) total = 1f;
            foreach (var it in src.m_items)
            {
                if (it == null || it.m_object == null) continue;
                var nested = it.m_object.GetComponent<SpawnGroup>();
                if (nested != null && nested != src) { AddItems(nested, scale * it.m_chance / total, into, ref big, ref all); continue; }
                float chance = it.m_chance * scale;
                into.Add(new SpawnItem { m_object = it.m_object, m_chance = chance });
                all++;
                var room = it.m_object.GetComponent<Room>();
                var b = room != null ? Big(room) : null;
                if (b != null) { into.Add(new SpawnItem { m_object = b.gameObject, m_chance = chance * BigWeight }); big++; }
            }
        }

        /// <summary>The big copy of <paramref name="prefab"/>, built the first time it is asked for; null if the room
        /// can't grow.</summary>
        public static Room Big(Room prefab)
        {
            if (prefab == null) return null;
            Room r;
            if (s_big.TryGetValue(prefab.gameObject, out r)) return r;
            r = null;
            if (Eligible(prefab))
            {
                try { r = Build(prefab); }
                catch (Exception e) { FurtherCore.Log.LogWarning("Chaos rooms: " + prefab.name + " stays its own size (" + e.Message + ")"); r = null; }
            }
            s_big[prefab.gameObject] = r;
            return r;
        }

        static bool Eligible(Room p)
        {
            return !p.m_corridor && !p.m_bossRoom && !p.m_isPortalRoom && !p.m_isPowerupRoom
                && !R.Get<bool>(p, "m_nonSquareBounds") && !NotRoom.IsMatch(p.name);
        }

        // ------------------------------------------------------------------ pictures

        /// <summary>A sprite's picture, cut from its atlas (bottom-up rows), and where its quad sits in room space.</summary>
        class Pic
        {
            public exSprite spr;
            public int w, h;
            public Color32[] px;
            public float left, bottom;   // room space
            public float Right { get { return left + w; } }
            public float Top { get { return bottom + h; } }

            public Color32 At(int x, int y) { return px[y * w + x]; }
        }

        static Texture2D Readable(Texture t)
        {
            Texture2D r;
            if (!s_readable.TryGetValue(t, out r) || r == null)
            {
                r = SpriteUtil.CopyTexture(t);
                SpriteSheets.Keep(r);
                s_readable[t] = r;
            }
            return r;
        }

        /// <summary>The quad's lower left corner in room space, as ex2D lays it out now.</summary>
        static Vector2 QuadMin(exSprite s, Transform room)
        {
            var m = new Mesh();
            var keep = s.updateFlags;
            s.updateFlags = exPlane.UpdateFlags.Vertex;
            s.UpdateMesh(m);
            s.updateFlags = keep;
            var v = m.vertices;
            UnityEngine.Object.DestroyImmediate(m);
            float x = float.MaxValue, y = float.MaxValue;
            foreach (var p in v)
            {
                var q = room.InverseTransformPoint(s.transform.TransformPoint(p));
                x = Mathf.Min(x, q.x); y = Mathf.Min(y, q.y);
            }
            return new Vector2(x, y);
        }

        static Pic Picture(exSprite s, Transform room)
        {
            var el = s.GetCurrentElement();
            if (el == null || el.rotated || s.atlas == null || s.atlas.texture == null) return null;
            var sc = s.transform.lossyScale;
            if (Mathf.Abs(Mathf.Abs(sc.x) - 1f) > 0.01f || Mathf.Abs(Mathf.Abs(sc.y) - 1f) > 0.01f || sc.x < 0f || sc.y < 0f) return null;
            if (s.isHFlipped || s.isVFlipped || s.customSize) return null;
            var t = Readable(s.atlas.texture);
            int x = Mathf.RoundToInt(el.coords.x * t.width), y = Mathf.RoundToInt(el.coords.y * t.height);
            int w = Mathf.RoundToInt(el.coords.width * t.width), h = Mathf.RoundToInt(el.coords.height * t.height);
            if (w < 2 || h < 2) return null;
            var at = QuadMin(s, room);
            return new Pic { spr = s, w = w, h = h, px = t.GetPixels32Block(x, y, w, h), left = Mathf.Round(at.x), bottom = Mathf.Round(at.y) };
        }

        static Color32[] GetPixels32Block(this Texture2D t, int x, int y, int w, int h)
        {
            var c = t.GetPixels(x, y, w, h);
            var o = new Color32[c.Length];
            for (int i = 0; i < c.Length; i++) o[i] = c[i];
            return o;
        }

        /// <summary>Put a grown picture on its sprite, its lower left corner kept where it was.</summary>
        static void Apply(Pic p, Transform room, string name)
        {
            var tex = new Texture2D(p.w, p.h, TextureFormat.ARGB32, false) { name = name, filterMode = FilterMode.Point, wrapMode = TextureWrapMode.Clamp };
            tex.SetPixels32(p.px);
            tex.Apply(false);
            var el = new exAtlas.Element
            {
                name = name, originalWidth = p.w, originalHeight = p.h,
                trimRect = new Rect(0f, 0f, p.w, p.h), coords = new Rect(0f, 0f, 1f, 1f), rotated = false,
            };
            var atlas = SpriteUtil.MakeAtlas(name, tex, new[] { el }, p.spr.atlas.material);
            var before = new Vector2(p.left, p.bottom);
            p.spr.SetSprite(atlas, 0);
            for (int i = 0; i < 2; i++)
            {
                var now = QuadMin(p.spr, room);
                var off = before - now;
                if (off.sqrMagnitude < 0.01f) break;
                p.spr.offset = p.spr.offset + off;
            }
            var end = QuadMin(p.spr, room) - before;
            if (end.sqrMagnitude > 0.01f) throw new Exception("could not place " + name + " (" + end + ")");
        }

        // ------------------------------------------------------------------ lines (columns, or rows on a transposed picture)

        class Img
        {
            public int w, h;
            public Color32[] p;
            public Img(int w, int h, Color32[] p) { this.w = w; this.h = h; this.p = p; }
            public Color32 At(int x, int y) { return p[y * w + x]; }
            public Img T()
            {
                var o = new Color32[p.Length];
                for (int y = 0; y < h; y++) for (int x = 0; x < w; x++) o[x * h + y] = p[y * w + x];
                return new Img(h, w, o);
            }
        }

        static bool[] SolidLines(Img im, int margin = 3)
        {
            var ok = new bool[im.w];
            for (int x = 0; x < im.w; x++)
            {
                bool s = true;
                for (int y = margin; y < im.h - margin && s; y++) if (im.At(x, y).a < 255) s = false;
                ok[x] = s;
            }
            return ok;
        }

        /// <summary>Per line, the floor after a 9-along by 5-across average (rows 4 in from each end dropped).</summary>
        static float[,,] Smoothed(Img im)
        {
            int w = im.w, h = im.h, rows = Mathf.Max(1, h - 8);
            var sm = new float[w, rows, 3];
            for (int x = 0; x < w; x++)
                for (int r = 0; r < rows; r++)
                {
                    int y = r + 4;
                    float a = 0, b = 0, c = 0;
                    int n = 0;
                    for (int dx = -2; dx <= 2; dx++)
                        for (int dy = -4; dy <= 4; dy++)
                        {
                            int xx = Mathf.Clamp(x + dx, 0, w - 1), yy = Mathf.Clamp(y + dy, 0, h - 1);
                            var q = im.At(xx, yy);
                            a += q.r; b += q.g; c += q.b; n++;
                        }
                    sm[x, r, 0] = a / n; sm[x, r, 1] = b / n; sm[x, r, 2] = c / n;
                }
            return sm;
        }

        /// <summary>How unlike line x is from line c: the largest smoothed difference down the line.</summary>
        static float Unlike(float[,,] sm, int c, int x)
        {
            int rows = sm.GetLength(1);
            float m = 0f;
            for (int r = 0; r < rows; r++)
            {
                float d = Mathf.Abs(sm[x, r, 0] - sm[c, r, 0]) + Mathf.Abs(sm[x, r, 1] - sm[c, r, 1]) + Mathf.Abs(sm[x, r, 2] - sm[c, r, 2]);
                if (d > m) m = d;
            }
            return m;
        }

        static float[] LikeRow(float[,,] sm, int c, int n)
        {
            var o = new float[n];
            for (int x = 0; x < n; x++) o[x] = Unlike(sm, c, x);
            return o;
        }

        static float LineDiff(Img a, int x, Img b, int y)
        {
            float s = 0f;
            for (int i = 0; i < a.h; i++)
            {
                var p = a.At(x, i); var q = b.At(y, i);
                s += Mathf.Abs(p.r - q.r) + Mathf.Abs(p.g - q.g) + Mathf.Abs(p.b - q.b) + Mathf.Abs(p.a - q.a);
            }
            return s;
        }

        /// <summary>Blocks (source line, width) filling <paramref name="amount"/> lines inserted before <paramref name="cut"/>.</summary>
        static List<int[]> Quilt(Img im, int cut, int amount, int lo, int hi, System.Random rnd, Func<int, int, bool> usable)
        {
            var blocks = new List<int[]>();
            int left = amount, prev = cut - 1;
            while (left > 0)
            {
                int want = Math.Min(left, rnd.Next(BlockMin, BlockMax + 1));
                if (left - want < MinBlock) want = left;
                int[] pick = null;
                int w = want;
                while (w > 0)
                {
                    bool last = w == left;
                    var cands = new List<KeyValuePair<float, int>>();
                    int s0 = Math.Max(lo + 1, cut - Window), s1 = Math.Min(hi - w + 1, cut + Window - w);
                    for (int s = s0; s < s1; s++)
                    {
                        if (!usable(s, w)) continue;
                        float score = LineDiff(im, prev, im, s - 1) + Near * Math.Abs(s - cut);
                        if (last) score += LineDiff(im, cut, im, s + w);
                        cands.Add(new KeyValuePair<float, int>(score, s));
                    }
                    if (cands.Count > 0)
                    {
                        cands.Sort((a, b) => a.Key.CompareTo(b.Key));
                        pick = new[] { cands[Math.Min(cands.Count - 1, rnd.Next(0, 2))].Value, w };
                        break;
                    }
                    if (w == left && left > 2 * MinBlock) w = left - MinBlock;
                    else w -= 4;
                    if (w < MinBlock) break;
                }
                if (pick == null) return null;
                blocks.Add(pick);
                prev = pick[0] + pick[1] - 1;
                left -= pick[1];
            }
            return blocks;
        }

        static Img InsertLines(Img im, int cut, List<int[]> blocks)
        {
            int add = 0;
            foreach (var b in blocks) add += b[1];
            int nw = im.w + add;
            var o = new Color32[nw * im.h];
            for (int y = 0; y < im.h; y++)
            {
                int dst = 0;
                for (int x = 0; x < cut; x++) o[y * nw + dst++] = im.At(x, y);
                foreach (var b in blocks) for (int x = b[0]; x < b[0] + b[1]; x++) o[y * nw + dst++] = im.At(Mathf.Clamp(x, 0, im.w - 1), y);
                for (int x = cut; x < im.w; x++) o[y * nw + dst++] = im.At(x, y);
            }
            return new Img(nw, im.h, o);
        }

        // ------------------------------------------------------------------ the room

        class Child
        {
            public Transform t;
            public string name;
            public bool hasExtent;
            public Rect ext;   // room space
        }

        static void Grow(ref Rect r, ref bool any, Rect add)
        {
            r = any ? Rect.MinMaxRect(Mathf.Min(r.xMin, add.xMin), Mathf.Min(r.yMin, add.yMin), Mathf.Max(r.xMax, add.xMax), Mathf.Max(r.yMax, add.yMax)) : add;
            any = true;
        }

        static Child Measure(Transform c, Transform room)
        {
            var ch = new Child { t = c, name = c.name };
            Rect r = new Rect();
            bool any = false;
            foreach (var s in c.GetComponentsInChildren<exSprite>(true))
            {
                if (s.atlas == null || s.GetCurrentElement() == null) continue;
                var at = QuadMin(s, room);
                Grow(ref r, ref any, new Rect(at.x, at.y, Mathf.Abs(s.width), Mathf.Abs(s.height)));
            }
            foreach (var col in c.GetComponentsInChildren<Collider>(true))
            {
                var b = WorldBox(col);
                if (b.width <= 0f && b.height <= 0f) continue;
                var mn = room.InverseTransformPoint(new Vector3(b.xMin, b.yMin, 0f));
                var mx = room.InverseTransformPoint(new Vector3(b.xMax, b.yMax, 0f));
                Grow(ref r, ref any, Rect.MinMaxRect(mn.x, mn.y, mx.x, mx.y));
            }
            if (!any)
            {
                var p = room.InverseTransformPoint(c.position);
                r = new Rect(p.x, p.y, 0f, 0f);
            }
            ch.hasExtent = any;
            ch.ext = r;
            return ch;
        }

        /// <summary>A collider's x/y footprint in world space, worked out from its shape (bounds are empty while the
        /// prefab copy is inactive).</summary>
        static Rect WorldBox(Collider c)
        {
            var t = c.transform;
            Vector3 center, half;
            var box = c as BoxCollider;
            var cap = c as CapsuleCollider;
            var sph = c as SphereCollider;
            if (box != null) { center = box.center; half = box.size * 0.5f; }
            else if (cap != null)
            {
                center = cap.center;
                float r = cap.radius, l = Mathf.Max(cap.height * 0.5f, r);
                half = cap.direction == 0 ? new Vector3(l, r, r) : cap.direction == 1 ? new Vector3(r, l, r) : new Vector3(r, r, l);
            }
            else if (sph != null) { center = sph.center; half = Vector3.one * sph.radius; }
            else return new Rect();
            var s = t.lossyScale;
            var w = t.TransformPoint(center);
            float hx = Mathf.Abs(half.x * s.x), hy = Mathf.Abs(half.y * s.y);
            return Rect.MinMaxRect(w.x - hx, w.y - hy, w.x + hx, w.y + hy);
        }

        class Plan
        {
            public Room room;
            public Transform tr;
            public List<Child> kids = new List<Child>();
            public Pic floor;
            public List<Pic> strips = new List<Pic>();
            public List<DoorData> doors;
        }

        static List<Vector2> Blockers(Plan P, int axis, bool source)
        {
            var o = new List<Vector2>();
            if (!source)
                foreach (var d in P.doors)
                {
                    bool sideWall = d.m_direction == DoorData.eDirection.Left || d.m_direction == DoorData.eDirection.Right;
                    if ((axis == 0) != sideWall)
                    {
                        float v = axis == 0 ? d.m_position.x : d.m_position.y;
                        o.Add(new Vector2(v - DoorClear, v + DoorClear));
                    }
                }
            foreach (var k in P.kids)
            {
                if (Skip.IsMatch(k.name)) continue;
                if (axis == 0 && Strip.IsMatch(k.name)) continue;
                if (source && Copy.IsMatch(k.name)) continue;
                float lo = axis == 0 ? k.ext.xMin : k.ext.yMin, hi = axis == 0 ? k.ext.xMax : k.ext.yMax;
                o.Add(new Vector2(lo + 1f, hi - 1f));
            }
            return o;
        }

        static bool Blocked(List<Vector2> bl, float v)
        {
            foreach (var b in bl) if (v >= b.x && v <= b.y) return true;
            return false;
        }

        static bool Overlaps(List<Vector2> bl, float a, float b)
        {
            foreach (var r in bl) if (a < r.y && b > r.x) return true;
            return false;
        }

        /// <summary>The seam on one axis (room space), or NaN. <paramref name="line0"/> is the room coordinate of line 0.</summary>
        static float Seam(Plan P, int axis, Img lines, bool[] solid, float[,,] sm, float line0, System.Random rnd)
        {
            float lo = line0 + Edge + 8f, hi = line0 + lines.w - Edge - 8f;
            if (axis == 1) hi = Mathf.Min(hi, line0 + lines.w * 0.5f + 12f);   // clear of the back wall's shadow
            var bl = Blockers(P, axis, false);
            var ok = new List<KeyValuePair<int, float>>();
            int best = 0;
            for (int v = Mathf.CeilToInt(lo); v < hi; v += 2)
            {
                int c = v - Mathf.RoundToInt(line0);
                if (c < 1 || c >= lines.w || Blocked(bl, v) || !solid[c] || !solid[c - 1]) continue;
                int n = 0;
                for (int x = Math.Max(0, c - Window); x < Math.Min(lines.w, c + Window); x++)
                    if (solid[x] && Unlike(sm, c, x) <= Alike) n++;
                ok.Add(new KeyValuePair<int, float>(v, n));
                best = Math.Max(best, n);
            }
            if (ok.Count == 0 || best < MinAlike) return float.NaN;
            float mid = (lo + hi) * 0.5f, pickD = float.MaxValue, pick = float.NaN;
            foreach (var kv in ok)
            {
                if (kv.Value < best * 0.85f) continue;
                float d = Mathf.Abs(kv.Key - mid) + (float)rnd.NextDouble() * 6f;
                if (d < pickD) { pickD = d; pick = kv.Key; }
            }
            return pick;
        }

        static Room Build(Room prefab)
        {
            var cb = prefab.m_cameraBounds;
            int dx = (int)(Mathf.Max(0f, Mathf.Min(MaxW - cb.width, cb.width * (GrowW - 1f))) / 2f) * 2;
            int dy = (int)(Mathf.Max(0f, Mathf.Min(MaxH - cb.height, cb.height * (GrowH - 1f))) / 2f) * 2;
            if (dx == 0 && dy == 0) return null;

            var go = MonsterFactory.ClonePrefab(prefab.gameObject, prefab.name);
            go.transform.position = Vector3.zero;
            var room = go.GetComponent<Room>();
            try
            {
                if (!Grow(room, prefab.name, dx, dy)) { UnityEngine.Object.DestroyImmediate(go); return null; }
            }
            catch
            {
                UnityEngine.Object.DestroyImmediate(go);
                throw;
            }
            return room;
        }

        static bool Grow(Room room, string name, int dx, int dy)
        {
            var rnd = new System.Random(name.GetHashCode());
            var P = new Plan { room = room, tr = room.transform, doors = room.m_doors };
            var floorSpr = room.GetComponent<exSprite>();
            if (floorSpr == null) return false;
            P.floor = Picture(floorSpr, P.tr);
            if (P.floor == null) return false;
            foreach (Transform c in P.tr)
            {
                var k = Measure(c, P.tr);
                P.kids.Add(k);
                if (Strip.IsMatch(k.name))
                {
                    var s = c.GetComponent<exSprite>();
                    var pic = s != null ? Picture(s, P.tr) : null;
                    if (pic != null) P.strips.Add(pic);
                }
            }
            var F = P.floor;
            var fimg = new Img(F.w, F.h, F.px);
            var solidX = SolidLines(fimg);
            var fT = fimg.T();
            var solidY = SolidLines(fT);
            var smX = dx > 0 ? Smoothed(fimg) : null;
            var smY = dy > 0 ? Smoothed(fT) : null;
            float sx = dx > 0 ? Seam(P, 0, fimg, solidX, smX, F.left, rnd) : float.NaN;
            float sy = dy > 0 ? Seam(P, 1, fT, solidY, smY, F.bottom, rnd) : float.NaN;
            if (float.IsNaN(sx)) dx = 0;
            if (float.IsNaN(sy)) dy = 0;
            if (dx == 0 && dy == 0) return false;

            // ---- x: the art
            List<int[]> xb = null;
            List<Pic> crossing = new List<Pic>();
            if (dx > 0)
            {
                int cut = Mathf.RoundToInt(sx - F.left);
                foreach (var s in P.strips) if (s.left < sx && s.Right > sx) crossing.Add(s);
                var lx = LikeRow(smX, cut, F.w);
                int lo = (int)(F.w * SrcX0), hi = (int)(F.w * SrcX1);
                foreach (var s in crossing) { lo = Math.Max(lo, Mathf.RoundToInt(s.left - F.left) + 2); hi = Math.Min(hi, Mathf.RoundToInt(s.Right - F.left) - 2); }
                var src = Blockers(P, 0, true);
                for (int i = 0; i < src.Count; i++) src[i] -= new Vector2(F.left, F.left);
                var comp = Composite(F, crossing);
                xb = Quilt(comp, cut, dx, lo, hi, rnd, (s, w) =>
                {
                    for (int x = s - 1; x <= s + w; x++)
                        if (x < 0 || x >= F.w || !solidX[x] || lx[x] > Alike) return false;
                    return !Overlaps(src, s - 1, s + w + 1);
                });
                if (xb == null) dx = 0;
            }
            // ---- y: the art (rows of the floor only)
            List<int[]> yb = null;
            if (dy > 0)
            {
                int cut = Mathf.RoundToInt(sy - F.bottom);
                var ly = LikeRow(smY, cut, F.h);
                var src = Blockers(P, 1, true);
                for (int i = 0; i < src.Count; i++) src[i] -= new Vector2(F.bottom, F.bottom);
                yb = Quilt(fT, cut, dy, (int)(F.h * SrcY0), (int)(F.h * SrcY1), rnd, (s, w) =>
                {
                    for (int y = s - 1; y <= s + w; y++)
                        if (y < 0 || y >= F.h || !solidY[y] || ly[y] > Alike) return false;
                    return !Overlaps(src, s - 1, s + w + 1);
                });
                if (yb == null) dy = 0;
            }
            if (dx == 0 && dy == 0) return false;

            // ---- pictures
            if (dx > 0)
            {
                int cut = Mathf.RoundToInt(sx - F.left);
                fimg = InsertLines(fimg, cut, xb);
                foreach (var s in crossing)
                {
                    int off = Mathf.RoundToInt(F.left - s.left);
                    var sb = new List<int[]>();
                    foreach (var b in xb) sb.Add(new[] { b[0] + off, b[1] });
                    var si = InsertLines(new Img(s.w, s.h, s.px), Mathf.RoundToInt(sx - s.left), sb);
                    s.w = si.w; s.px = si.p;
                }
            }
            if (dy > 0)
            {
                var t = fimg.T();
                t = InsertLines(t, Mathf.RoundToInt(sy - F.bottom), yb);
                fimg = t.T();
            }
            F.w = fimg.w; F.h = fimg.h; F.px = fimg.p;
            Apply(F, P.tr, "Chaos_" + name + "_floor");
            int n = 0;
            foreach (var s in crossing) Apply(s, P.tr, "Chaos_" + name + "_wall" + (n++));

            // ---- everything else
            if (dx > 0) Move(P, 0, sx, dx, xb, F.left, crossing);
            if (dy > 0) Move(P, 1, sy, dy, null, F.bottom, null);

            float ratio = (cbArea(room.m_cameraBounds, dx, dy)) / Mathf.Max(1f, room.m_cameraBounds.width * room.m_cameraBounds.height);
            var cbn = room.m_cameraBounds;
            cbn.width += dx; cbn.height += dy;
            room.m_cameraBounds = cbn;
            MoreContent(room, ratio);
            var tag = room.gameObject.AddComponent<ChaosRoomTag>();
            tag.area = ratio;
            FurtherCore.Log.LogInfo("Chaos: " + name + " grows to " + cbn.width + " x " + cbn.height + (dx > 0 ? " (seam x " + sx + ")" : "") + (dy > 0 ? " (seam y " + sy + ")" : ""));
            return true;
        }

        static float cbArea(Rect cb, int dx, int dy) { return (cb.width + dx) * (cb.height + dy); }

        static Img Composite(Pic floor, List<Pic> strips)
        {
            float top = floor.Top;
            foreach (var s in strips) top = Mathf.Max(top, s.Top);
            int h = Mathf.RoundToInt(top - floor.bottom), w = floor.w;
            var o = new Color32[w * h];
            Paste(o, w, h, floor, 0, 0);
            foreach (var s in strips) Paste(o, w, h, s, Mathf.RoundToInt(s.left - floor.left), Mathf.RoundToInt(s.bottom - floor.bottom));
            return new Img(w, h, o);
        }

        static void Paste(Color32[] o, int w, int h, Pic p, int ox, int oy)
        {
            for (int y = 0; y < p.h; y++)
            {
                int yy = y + oy;
                if (yy < 0 || yy >= h) continue;
                for (int x = 0; x < p.w; x++)
                {
                    int xx = x + ox;
                    if (xx < 0 || xx >= w) continue;
                    var s = p.At(x, y);
                    if (s.a == 0) continue;
                    var d = o[yy * w + xx];
                    float a = s.a / 255f;
                    o[yy * w + xx] = new Color32((byte)(s.r * a + d.r * (1 - a)), (byte)(s.g * a + d.g * (1 - a)), (byte)(s.b * a + d.b * (1 - a)), (byte)Mathf.Max(s.a, d.a));
                }
            }
        }

        static float Along(Vector3 v, int axis) { return axis == 0 ? v.x : v.y; }

        static Vector3 Step(int axis, float d) { return axis == 0 ? new Vector3(d, 0f, 0f) : new Vector3(0f, d, 0f); }

        /// <summary>Move, lengthen and copy what the seam on <paramref name="axis"/> affects.</summary>
        static void Move(Plan P, int axis, float seam, int d, List<int[]> blocks, float line0, List<Pic> rebuilt)
        {
            var tr = P.tr;
            var step = Step(axis, d);
            var copies = new List<KeyValuePair<Transform, Vector3>>();
            foreach (var k in P.kids)
            {
                if (k.name == "RoomBounds") continue;
                if (k.name == "Walls" || k.name == "WallsTop")
                {
                    foreach (Transform w in k.t)
                    {
                        var box = w.GetComponent<BoxCollider>();
                        var c = tr.InverseTransformPoint(box != null ? w.TransformPoint(box.center) : w.position);
                        float half = box != null ? Mathf.Abs(Along(Vector3.Scale(box.size, w.lossyScale), axis)) * 0.5f : 0f;
                        float mid = Along(c, axis);
                        if (box != null && mid - half < seam && mid + half > seam)
                        {
                            var ls = w.localScale;
                            float per = Mathf.Abs(Along(Vector3.Scale(box.size, w.lossyScale), axis)) / Mathf.Max(0.0001f, Mathf.Abs(Along(ls, axis)));
                            if (axis == 0) ls.x += Mathf.Sign(ls.x) * d / per; else ls.y += Mathf.Sign(ls.y) * d / per;
                            w.localScale = ls;
                            w.position += step * 0.5f;
                        }
                        else if (mid > seam) w.position += step;
                    }
                    continue;
                }
                bool rebuiltHere = false;
                if (rebuilt != null) foreach (var s in rebuilt) if (s.spr.transform == k.t) rebuiltHere = true;
                if (rebuiltHere) continue;
                float lo = axis == 0 ? k.ext.xMin : k.ext.yMin, hi = axis == 0 ? k.ext.xMax : k.ext.yMax;
                if (lo >= seam || (!k.hasExtent && lo > seam)) { k.t.position += step; continue; }
                if (blocks != null && hi <= seam && Copy.IsMatch(k.name))
                {
                    float dst = seam;
                    foreach (var b in blocks)
                    {
                        float s0 = b[0] + line0;
                        if (lo >= s0 && hi <= s0 + b[1]) copies.Add(new KeyValuePair<Transform, Vector3>(k.t, Step(axis, dst - s0)));
                        dst += b[1];
                    }
                }
            }
            foreach (var c in copies)
            {
                bool was = c.Key.gameObject.activeSelf;
                c.Key.gameObject.SetActive(false);
                var o = (GameObject)UnityEngine.Object.Instantiate(c.Key.gameObject);
                c.Key.gameObject.SetActive(was);
                o.transform.SetParent(c.Key.parent, true);
                o.SetActive(was);
                o.name = c.Key.name;
                o.transform.position = c.Key.position + c.Value;
                if (o.transform.parent == tr) P.kids.Add(Measure(o.transform, tr));
            }
            // the room's outline, its meshes and its doors
            var shape = tr.GetComponentInChildren<CollisionShape2D>(true);
            if (shape != null)
            {
                var off = (Vector2)tr.InverseTransformPoint(shape.transform.position);
                for (int i = 0; i < shape.m_points.Count; i++)
                {
                    var p = shape.m_points[i];
                    if (Along(p + off, axis) > seam) shape.m_points[i] = p + (Vector2)step;
                }
                shape.m_visualMesh = ShiftMesh(shape.m_visualMesh, axis, seam - Along(off, axis), d);
                var oldCol = shape.m_collisionMesh;
                shape.m_collisionMesh = ShiftMesh(shape.m_collisionMesh, axis, seam - Along(off, axis), d);
                foreach (var mc in shape.GetComponents<MeshCollider>()) if (mc.sharedMesh == oldCol) mc.sharedMesh = shape.m_collisionMesh;
                foreach (var mf in shape.GetComponents<MeshFilter>()) mf.sharedMesh = shape.m_visualMesh;
            }
            foreach (var door in P.doors)
                if (Along(door.m_position, axis) > seam) door.m_position += (Vector2)step;
        }

        static Mesh ShiftMesh(Mesh m, int axis, float seam, int d)
        {
            if (m == null) return null;
            var o = UnityEngine.Object.Instantiate(m);
            o.name = m.name;
            var v = o.vertices;
            for (int i = 0; i < v.Length; i++) if (Along(v[i], axis) > seam) v[i] += Step(axis, d);
            o.vertices = v;
            o.RecalculateBounds();
            SpriteSheets.Keep(o);
            return o;
        }

        static void MoreContent(Room room, float ratio)
        {
            room.m_maxDecalProps = Scaled(room.m_maxDecalProps, ratio);
            room.m_maxSmallProps = Scaled(room.m_maxSmallProps, ratio);
            room.m_maxLargeProps = Scaled(room.m_maxLargeProps, ratio);
            room.m_maxFeatureProps = Scaled(room.m_maxFeatureProps, Mathf.Sqrt(ratio));
            room.m_maxTraps = Mathf.RoundToInt(room.m_maxTraps * ratio);
            room.m_maxCrystals = Mathf.RoundToInt(room.m_maxCrystals * ratio);
            room.m_maxStatues = Mathf.RoundToInt(room.m_maxStatues * Mathf.Sqrt(ratio));
            room.m_maxDifficulty *= ratio;
            var e = R.Get<int[]>(room, "m_maxEnemiesBalanced");
            if (e != null)
            {
                var n = new int[e.Length];
                for (int i = 0; i < e.Length; i++) n[i] = Mathf.CeilToInt(e[i] * (1f + (ratio - 1f) * EnemyGrowth));
                R.Set(room, "m_maxEnemiesBalanced", n);
            }
        }

        static MinMaxRange Scaled(MinMaxRange m, float k)
        {
            if (m == null) return null;
            var o = new MinMaxRange(m);
            o.m_min *= k;
            o.m_max *= k;
            return o;
        }

        /// <summary>Self-test: the patched game members are there.</summary>
        public static void SelfCheck(Action<string> bad)
        {
            foreach (var f in new[] { "m_nonSquareBounds", "m_maxEnemiesBalanced", "m_walls" })
                if (AccessTools.Field(typeof(Room), f) == null) bad("chaos rooms: Room." + f + " missing");
            if (AccessTools.Field(typeof(CollisionShape2D), "m_collisionMesh") == null) bad("chaos rooms: CollisionShape2D.m_collisionMesh missing");
            if (AccessTools.Method(typeof(Environment), "GetRoomGroup") == null) bad("chaos rooms: Environment.GetRoomGroup missing");
            if (AccessTools.Method(typeof(Room), "SpawnEnemySpawners") == null) bad("chaos rooms: Room.SpawnEnemySpawners missing");
        }
    }

    /// <summary>Marks a big chaos room (on its prefab copy and so on every room spawned from it).</summary>
    public class ChaosRoomTag : MonoBehaviour
    {
        /// <summary>Its camera frame's area over the original room's.</summary>
        public float area = 1f;
    }

    [HarmonyPatch(typeof(Environment), "GetRoomGroup")]
    static class Patch_ChaosRoomGroup
    {
        static void Postfix(ref SpawnGroup __result) { if (ChaosRooms.Enabled && ChaosMode.Active) __result = ChaosRooms.GroupFor(__result); }
    }

    [HarmonyPatch(typeof(Environment), "GetRoomGroupStarting")]
    static class Patch_ChaosRoomGroupStarting
    {
        static void Postfix(ref SpawnGroup __result) { if (ChaosRooms.Enabled && ChaosMode.Active) __result = ChaosRooms.GroupFor(__result); }
    }

    [HarmonyPatch(typeof(Room), "SpawnEnemySpawners")]
    static class Patch_ChaosRoomEnemies
    {
        static void Prefix(Room __instance, ref int baseEnemyCount)
        {
            var tag = __instance != null ? __instance.GetComponent<ChaosRoomTag>() : null;
            if (tag != null && tag.area > 1f) baseEnemyCount = Mathf.CeilToInt(baseEnemyCount * (1f + (tag.area - 1f) * ChaosRooms.EnemyGrowth));
        }
    }
}
