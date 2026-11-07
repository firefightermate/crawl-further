using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.UI
{
    using CrawlFurther.Art;
    using CrawlFurther.Monsters;

    /// <summary>
    /// The violet gem that marks mod content in the menus: a 5 x 5 sprite (sheet ModBadgeGem) of its own, drawn in front
    /// of the picture it marks and never clipped with it. When the picture sits in a clipped tile, the gem moves inside the
    /// visible part of the tile. Anything drawn from a sheet loaded through Core counts as mod content, so any mod's
    /// monsters, items and portraits are marked without extra work; <see cref="Exclude"/> leaves a sheet unmarked.
    ///
    /// Gems are placed only through <see cref="ModMark"/>, which decides who owns the mark of each picture:
    /// <see cref="Attach"/> follows a menu sprite (a monster tile, a portrait, a shop bubble) and shows the gem whenever
    /// that sprite shows mod art; <see cref="AttachAt"/> pins one to a fixed spot (a vault cell corner) and leaves showing
    /// it to the caller.
    /// </summary>
    public class ModGem : MonoBehaviour
    {
        const string SheetId = "ModBadgeGem";
        const float Half = 2.5f;          // the gem is 5 x 5
        const float InFront = 1f;         // world units nearer the camera than the sprite it marks

        static exAtlas s_atlas;
        static readonly HashSet<string> s_excluded = new HashSet<string>
        {
            SheetId, "VaultIcons", "ModVioletPip", "ModSpellPip", "ModBothPip", "SlotLockOverlay",
            "SlotPipSilver", "SlotPipGold", "SlotPipSilverLocked", "SlotPipGoldLocked",
        };
        static readonly Dictionary<long, int[]> s_bounds = new Dictionary<long, int[]>();

        exSprite m_target;
        Renderer m_targetR, m_r, m_follow;
        GemCorner m_corner;
        Func<bool> m_show;
        bool m_fixed;

        /// <summary>For <see cref="AttachAt"/> gems: shown while true (and while the followed renderer is on).</summary>
        public bool On;

        /// <summary>Never mark frames of this sheet (a vanilla choice drawn as a mod sheet, or UI art).</summary>
        public static void Exclude(string sheetId) { if (!string.IsNullOrEmpty(sheetId)) s_excluded.Add(sheetId); }

        /// <summary>True when <paramref name="atlas"/> is a mod sheet's atlas that is not excluded.</summary>
        public static bool IsModArt(exAtlas atlas)
        {
            if (ModMark.IsRuntimeArt(atlas)) return true;
            var sh = SpriteSheets.ByAtlas(atlas);
            return sh != null && !s_excluded.Contains(sh.id);
        }

        /// <summary>
        /// Mark <paramref name="target"/> whenever it shows mod art (or whenever <paramref name="show"/> says so, if
        /// given). Safe to call every time the sprite is set up: a sprite gets one gem.
        /// </summary>
        internal static ModGem Attach(exSprite target, GemCorner corner = GemCorner.Art, Func<bool> show = null)
        {
            if (target == null || Atlas() == null) return null;
            // a gem copied along with its sprite (Instantiate) is found here too: it is claimed, not doubled
            var g = Find(target.transform, false) ?? Make(target.transform);
            g.m_target = target;
            g.m_targetR = target.GetComponent<Renderer>();
            g.m_corner = corner;
            g.m_show = show;
            return g;
        }

        /// <summary>A gem at a fixed local position under <paramref name="parent"/>, shown while <see cref="On"/> is set and
        /// <paramref name="follow"/> (if given) is drawn. Safe to call again: a parent gets one gem.</summary>
        internal static ModGem AttachAt(Transform parent, Vector3 localPos, Renderer follow)
        {
            if (parent == null || Atlas() == null) return null;
            var g = Find(parent, true) ?? Make(parent);
            g.m_fixed = true;
            g.m_follow = follow;
            g.transform.localPosition = localPos;
            return g;
        }

        /// <summary>A gem pinned with <see cref="AttachAt"/> (not following a sprite).</summary>
        internal bool Pinned { get { return m_fixed; } }

        static ModGem Find(Transform parent, bool pinned)
        {
            for (int i = 0; i < parent.childCount; i++)
            {
                var g = parent.GetChild(i).GetComponent<ModGem>();
                if (g != null && g.m_fixed == pinned && g.gameObject.activeSelf) return g;   // an inactive one is being taken away
            }
            return null;
        }

        static ModGem Make(Transform parent)
        {
            var go = new GameObject("ModGem");
            go.layer = parent.gameObject.layer;
            go.transform.SetParent(parent, false);
            go.AddComponent<MeshFilter>();
            go.AddComponent<MeshRenderer>();
            var spr = go.AddComponent<exSprite>();
            spr.anchor = exPlane.Anchor.MidCenter;
            spr.useTextureOffset = false;
            spr.SetSprite(Atlas(), 0);
            var r = go.GetComponent<Renderer>();
            r.sharedMaterial = Atlas().material;
            r.enabled = false;
            var g = go.AddComponent<ModGem>();
            g.m_r = r;
            return g;
        }

        static exAtlas Atlas()
        {
            if (s_atlas != null) return s_atlas;
            var sh = SpriteSheets.Get(SheetId);
            s_atlas = sh != null ? sh.atlas : null;
            return s_atlas;
        }

        void LateUpdate()
        {
            // a gem copied along with its parent (Instantiate) has none of its fields: it hides until Attach claims it
            if (m_r == null) m_r = GetComponent<Renderer>();
            bool show = ModMark.Enabled && (m_fixed ? FixedVisible() : Place());
            if (m_r.enabled != show) m_r.enabled = show;
        }

        bool FixedVisible()
        {
            if (!On) return false;
            return m_follow == null || (m_follow.enabled && m_follow.gameObject.activeInHierarchy);
        }

        /// <summary>Put the gem on the target's corner; false when it should not show.</summary>
        bool Place()
        {
            if (m_target == null || m_targetR == null || !m_targetR.enabled || !m_target.gameObject.activeInHierarchy) return false;
            if (m_target.atlas == null || m_target.index < 0) return false;
            if (m_show != null) { if (!m_show()) return false; }
            else if (!IsModArt(m_target.atlas)) return false;

            var rb = m_targetR.bounds;
            Vector2 at = new Vector2(1f, 1f);   // the gem's centre as a share of the target's quad, from its bottom-left
            var sh = SpriteSheets.ByAtlas(m_target.atlas);
            int[] bb;
            if (sh == null && ModMark.IsRuntimeArt(m_target.atlas) && m_target.index < m_target.atlas.elements.Length)
            {
                // run-time art (ModMark.MarkArt: framed portraits, untrimmed): the cell's corner, sized by the element
                var el = m_target.atlas.elements[m_target.index];
                float W = Mathf.Max(1, el.originalWidth), H = Mathf.Max(1, el.originalHeight);
                at = new Vector2((W - 3.5f) / W, (H - 3.5f) / H);
            }
            else if (sh != null)
            {
                float W = sh.manifest.cellW, H = sh.manifest.cellH;
                if (m_corner == GemCorner.Cell)
                    at = new Vector2((W - 3.5f) / W, (H - 3.5f) / H);
                else if (TryBounds(sh, m_target.index, Key(m_target.atlas, m_target.index), out bb))
                    // over the art's last column and centred on its top row, kept inside the cell
                    at = new Vector2(Mathf.Min(bb[0] + bb[2] + 1.5f, W - Half) / W, Mathf.Min(bb[1] + bb[3] - 0.5f, H - Half) / H);
            }
            // else a vanilla frame: it is trimmed to its pixels, so the quad's corner is the art's
            if (m_target.isHFlipped) at.x = 1f - at.x;
            var p = new Vector3(rb.min.x + at.x * rb.size.x, rb.min.y + at.y * rb.size.y, m_target.transform.position.z - InFront);

            var clip = m_target.clippingPlane;
            if (clip != null)
            {
                // in a clipped tile: keep the whole gem inside the part of the tile that shows
                Rect win = WorldRect(clip);
                p.x = Mathf.Clamp(Mathf.Min(p.x, win.xMax), win.xMin + Half, win.xMax - Half);
                p.y = Mathf.Clamp(Mathf.Min(p.y, win.yMax), win.yMin + Half, win.yMax - Half);
            }
            // on whole pixels: the 5 x 5 gem's centre sits on a pixel centre
            p.x = Mathf.Floor(p.x) + 0.5f;
            p.y = Mathf.Floor(p.y) + 0.5f;
            transform.position = p;
            return true;
        }

        static Rect WorldRect(exClipping clip)
        {
            var r = clip.clippedRect;
            Vector3 a = clip.transform.TransformPoint(new Vector3(r.xMin, r.yMin, 0f));
            Vector3 b = clip.transform.TransformPoint(new Vector3(r.xMax, r.yMax, 0f));
            return Rect.MinMaxRect(Mathf.Min(a.x, b.x), Mathf.Min(a.y, b.y), Mathf.Max(a.x, b.x), Mathf.Max(a.y, b.y));
        }

        static long Key(exAtlas a, int index) { return ((long)a.GetInstanceID() << 20) ^ (uint)index; }

        static bool TryBounds(SpriteSheet sh, int index, long k, out int[] bb)
        {
            if (s_bounds.TryGetValue(k, out bb)) return bb != null;
            int x, y, w, h;
            bb = MonsterFactory.Bounds(sh, index, out x, out y, out w, out h) ? new[] { x, y, w, h } : null;
            s_bounds[k] = bb;
            return bb != null;
        }

        /// <summary>Self-test: the gem's art.</summary>
        public static void SelfCheck(Action<string> bad)
        {
            var sh = SpriteSheets.Get(SheetId);
            if (sh == null) bad(SheetId + " art missing (mod content is marked with it)");
            else if (sh.manifest.cellW != 5 || sh.manifest.cellH != 5) bad(SheetId + " is not 5 x 5");
        }
    }
}
