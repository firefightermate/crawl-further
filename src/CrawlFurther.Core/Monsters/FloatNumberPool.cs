using UnityEngine;

namespace CrawlFurther.Monsters
{
    using CrawlFurther.Art;
    using CrawlFurther.Util;

    /// <summary>The pool behind <see cref="FloatNumber"/>: one root object, a fixed set of pop-ups, each a few glyph
    /// sprites. Rebuilt if a scene load destroys it.</summary>
    internal class FloatNumberPool : MonoBehaviour
    {
        const int PoolSize = 24, MaxGlyphs = 6;
        const float Depth = -30f;               // DepthHandler keeps characters within z -5..5 (plus small offsets)
        const float FlashTime = 0.08f;
        const float NearX = 12f, NearY = 10f, YoungAge = 0.55f, Spread = 11f, StackLift = 3f;   // sized for the 7 px digits
        const string Glyphs = "0123456789DOGE";
        static readonly string[] ToneNames = { "Normal", "Max", "Min", "Flash" };
        const int FlashTone = 3;

        static FloatNumberPool s_inst;
        static bool s_failed, s_logged;

        class Popup
        {
            public GameObject go;
            public Transform tr;
            public exSprite[] spr = new exSprite[MaxGlyphs];
            public int[] glyph = new int[MaxGlyphs];
            public int count;
            public int tone, shownTone = -1;
            public float t, alpha = -1f;
            public Vector2 anchor;   // where it was asked for (stacking test)
            public Vector2 origin;   // anchor plus the sideways shift
            public bool live;
        }

        readonly Popup[] m_pool = new Popup[PoolSize];
        SpriteSheet m_sheet;
        int[,] m_frame;              // [tone, glyph] -> cell index
        int[] m_bx, m_bw;            // per glyph: opaque left edge and width in the cell (same for every tone)

        public static void LogOnce(System.Exception e)
        {
            if (s_logged) return;
            s_logged = true;
            FurtherCore.Log.LogError("FloatNumber: " + e);
        }

        public static FloatNumberPool Get()
        {
            if (s_inst != null) return s_inst;
            if (s_failed) return null;
            var go = new GameObject("CrawlMod_FloatNumbers");
            s_inst = go.AddComponent<FloatNumberPool>();
            if (!s_inst.Build()) { s_failed = true; Destroy(go); s_inst = null; }
            return s_inst;
        }

        bool Build()
        {
            m_sheet = SpriteSheets.Get(FloatNumber.Sheet);
            if (m_sheet == null || m_sheet.atlas == null) { FurtherCore.Log.LogWarning("FloatNumber: " + FloatNumber.Sheet + " missing"); return false; }
            m_frame = new int[ToneNames.Length, Glyphs.Length];
            m_bx = new int[Glyphs.Length]; m_bw = new int[Glyphs.Length];
            for (int t = 0; t < ToneNames.Length; t++)
                for (int g = 0; g < Glyphs.Length; g++)
                {
                    var a = m_sheet.Anim(ToneNames[t] + Glyphs[g]);
                    if (a == null || a.frames == null || a.frames.Length == 0) { FurtherCore.Log.LogWarning("FloatNumber: no " + ToneNames[t] + Glyphs[g]); return false; }
                    m_frame[t, g] = a.frames[0];
                    if (t == 0)
                    {
                        int bx, by, bw, bh;
                        if (MonsterFactory.Bounds(m_sheet, a.frames[0], out bx, out by, out bw, out bh)) { m_bx[g] = bx; m_bw[g] = bw; }
                        else { m_bx[g] = 1; m_bw[g] = 7; }
                    }
                }
            for (int i = 0; i < PoolSize; i++)
            {
                var p = new Popup();
                p.go = new GameObject("ModFloatNumber");
                p.go.layer = 0;
                p.tr = p.go.transform;
                p.tr.SetParent(transform, false);
                for (int k = 0; k < MaxGlyphs; k++)
                {
                    var g = new GameObject("Glyph");
                    g.layer = 0;
                    g.transform.SetParent(p.tr, false);
                    g.AddComponent<MeshFilter>();
                    g.AddComponent<MeshRenderer>();
                    var s = g.AddComponent<exSprite>();
                    s.anchor = exPlane.Anchor.BotLeft;
                    s.SetSprite(m_sheet.atlas, m_frame[0, 0]);
                    p.spr[k] = s;
                }
                p.go.SetActive(false);
                m_pool[i] = p;
            }
            return true;
        }

        public void Spawn(string text, NumberTone tone, Vector2 at, GameObject like)
        {
            if (string.IsNullOrEmpty(text)) return;
            // the oldest live pop-up gives way when the pool is full
            Popup p = null;
            for (int i = 0; i < PoolSize; i++)
            {
                var q = m_pool[i];
                if (!q.live) { p = q; break; }
                if (p == null || q.t > p.t) p = q;
            }
            int n = 0;
            for (int i = 0; i < text.Length && n < MaxGlyphs; i++)
            {
                int g = Glyphs.IndexOf(char.ToUpperInvariant(text[i]));
                if (g >= 0) p.glyph[n++] = g;
            }
            if (n == 0) return;
            // numbers that land together (two dice on the hero, a swing through a crowd) stand side by side
            int near = 0;
            for (int i = 0; i < PoolSize; i++)
            {
                var q = m_pool[i];
                if (q == p || !q.live || q.t > YoungAge) continue;
                if (Mathf.Abs(q.anchor.x - at.x) < NearX && Mathf.Abs(q.anchor.y - at.y) < NearY) near++;
            }
            float dx = near == 0 ? 0f : ((near & 1) == 1 ? 1f : -1f) * ((near + 1) / 2) * Spread;
            p.anchor = at;
            // a neighbour also sits a little higher, so two dice never read as one two-digit number
            p.origin = new Vector2(at.x + dx, at.y + (near == 0 ? 0f : StackLift));
            p.count = n;
            p.tone = (int)tone;
            p.shownTone = -1;
            p.t = 0f;
            p.alpha = -1f;
            p.live = true;
            // lay the glyphs out centred on the origin, outlines overlapping by a pixel
            int width = 0;
            for (int k = 0; k < n; k++) width += m_bw[p.glyph[k]] - (k > 0 ? 1 : 0);
            int pen = -(width / 2);
            Camera cam = null;
            var ls = like != null ? like.GetComponent<exSprite>() : null;
            if (ls != null) cam = ls.renderCamera;
            if (cam == null)
            {
                var hero = ModUtil.Hero();
                var hs = hero != null ? hero.GetComponent<exSprite>() : null;
                if (hs != null) cam = hs.renderCamera;
            }
            if (cam == null) cam = Camera.main;
            for (int k = 0; k < MaxGlyphs; k++)
            {
                var s = p.spr[k];
                bool on = k < n;
                if (s.gameObject.activeSelf != on) s.gameObject.SetActive(on);
                if (!on) continue;
                int g = p.glyph[k];
                // the shadow row is 2 px above the cell bottom: the number's visible bottom sits on the origin
                s.transform.localPosition = new Vector3(pen - m_bx[g], -2f, -0.001f * k);
                pen += m_bw[g] - 1;
                if (cam != null && s.renderCameraForPrefab != cam) s.renderCamera = cam;
                // re-commit the whole quad: a pool built before the level camera existed never got its first commit
                s.updateFlags |= exPlane.UpdateFlags.Vertex | exPlane.UpdateFlags.UV | exPlane.UpdateFlags.Color | exPlane.UpdateFlags.Index;
            }
            if (!p.go.activeSelf) p.go.SetActive(true);
            Apply(p);
        }

        /// <summary>Height above the origin at time t: springs up 9 px, bounces back to 6, then drifts up to 24.</summary>
        public static float Rise(float t)
        {
            if (t < 0.14f) { float u = t / 0.14f; return 9f * (1f - (1f - u) * (1f - u)); }
            if (t < 0.24f) { float u = (t - 0.14f) / 0.10f; return 9f - 3f * u * u; }
            return 6f + 18f * Mathf.Clamp01((t - 0.24f) / (FloatNumber.Life - 0.24f));
        }

        public static float Alpha(float t)
        {
            const float fadeFrom = 0.55f;
            return t < fadeFrom ? 1f : Mathf.Clamp01(1f - (t - fadeFrom) / (FloatNumber.Life - fadeFrom));
        }

        void Apply(Popup p)
        {
            float t = p.t;
            int tone = t < FlashTime ? FlashTone : p.tone;
            float a = Alpha(t);
            float y = Mathf.Round(p.origin.y + Rise(t));
            p.tr.position = new Vector3(Mathf.Round(p.origin.x), y, Depth);
            if (tone != p.shownTone)
            {
                p.shownTone = tone;
                for (int k = 0; k < p.count; k++) p.spr[k].SetSprite(m_sheet.atlas, m_frame[tone, p.glyph[k]]);
            }
            if (Mathf.Abs(a - p.alpha) > 0.01f)
            {
                p.alpha = a;
                var c = new Color(1f, 1f, 1f, a);
                for (int k = 0; k < p.count; k++) p.spr[k].color = c;
            }
        }

        void LateUpdate()
        {
            float dt = Time.deltaTime;
            for (int i = 0; i < PoolSize; i++)
            {
                var p = m_pool[i];
                if (p == null || !p.live) continue;
                p.t += dt;
                if (p.t >= FloatNumber.Life)
                {
                    p.live = false;
                    p.go.SetActive(false);
                    continue;
                }
                try { Apply(p); }
                catch (System.Exception e) { LogOnce(e); p.live = false; p.go.SetActive(false); }
            }
        }

        void OnDestroy() { if (s_inst == this) s_inst = null; }
    }
}
