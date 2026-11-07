using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    using CrawlFurther.Util;

    /// <summary>
    /// Shard Hermit. Plant Crystal (his special, the YsvPlantCrystal clip event) plants a crystal spike near the hero; he
    /// keeps three at most (the oldest melts). Triangle: with three up, beads of light run between them and the floor
    /// inside frosts over, and a hero inside gets a frost pip every second. His crystals melt when he dies.
    /// </summary>
    public class HermitTriangle : YsveldBehaviour
    {
        public const int Max = 3;
        public const float Life = 30f, Tick = 1f, MaxSide = 170f, LinkGap = 9f, FrostGap = 14f;

        class Crystal { public GameObject go; public Vector2 at; public float born; }

        readonly List<Crystal> m_crystals = new List<Crystal>();
        readonly List<GameObject> m_links = new List<GameObject>(), m_frost = new List<GameObject>();
        bool m_formed;
        float m_tick;

        protected override void OnEnable() { base.OnEnable(); m_formed = false; m_tick = Tick; }

        protected override void OnDisable() { base.OnDisable(); while (m_crystals.Count > 0) Melt(0); ClearTriangle(); }

        /// <summary>Clip event: plant a crystal 10-22 px from the hero, on his side of any wall.</summary>
        public void YsvPlantCrystal()
        {
            if (!Alive || YsveldFx.HermitCrystal == null) return;
            var hero = HeroPos;
            var off = (Vector2)(Quaternion.Euler(0f, 0f, Random.Range(0f, 360f)) * Vector2.right) * Random.Range(10f, 22f);
            var at = ModUtil.SafePoint(hero, hero + new Vector2(off.x, off.y * 0.7f));
            var go = Show(YsveldFx.HermitCrystal, at);
            if (go == null) return;
            m_crystals.Add(new Crystal { go = go, at = at, born = Time.time });
            if (m_crystals.Count > Max) Melt(0);
            Rebuild();
        }

        void Melt(int i)
        {
            var c = m_crystals[i];
            m_crystals.RemoveAt(i);
            if (c.go != null && c.go.activeInHierarchy)
            {
                SystemPool.Despawn(c.go);
                Show(YsveldFx.HermitCrystalMelt, c.at);
            }
            Rebuild();
        }

        void ClearTriangle()
        {
            foreach (var g in m_links) if (g != null) SystemPool.Despawn(g);
            foreach (var g in m_frost) if (g != null) SystemPool.Despawn(g);
            m_links.Clear(); m_frost.Clear();
            m_formed = false;
        }

        void Rebuild()
        {
            ClearTriangle();
            if (m_crystals.Count < Max) return;
            Vector2 a = m_crystals[0].at, b = m_crystals[1].at, c = m_crystals[2].at;
            if ((a - b).magnitude > MaxSide || (b - c).magnitude > MaxSide || (c - a).magnitude > MaxSide) return;
            if (Mathf.Abs(Cross(b - a, c - a)) < 60f) return;      // three in a row: no floor between them
            m_formed = true;
            m_tick = Tick;
            // the lines: beads of light every 9 px along each side, a little above the floor
            foreach (var e in new[] { new[] { a, b }, new[] { b, c }, new[] { c, a } })
            {
                int n = Mathf.Max(1, Mathf.FloorToInt((e[1] - e[0]).magnitude / LinkGap));
                for (int k = 1; k < n; k++)
                {
                    var g = YsvUtil.Floor(YsveldFx.TriangleLink, Vector2.Lerp(e[0], e[1], k / (float)n) + new Vector2(0f, 1f));
                    if (g != null) m_links.Add(g);
                }
            }
            // the frosted floor: patches on a grid inside the triangle
            float x0 = Mathf.Min(a.x, Mathf.Min(b.x, c.x)), x1 = Mathf.Max(a.x, Mathf.Max(b.x, c.x));
            float y0 = Mathf.Min(a.y, Mathf.Min(b.y, c.y)), y1 = Mathf.Max(a.y, Mathf.Max(b.y, c.y));
            for (float y = y0 + FrostGap * 0.35f; y < y1; y += FrostGap * 0.5f)
                for (float x = x0 + FrostGap * 0.5f; x < x1; x += FrostGap)
                {
                    var p = new Vector2(x + ((int)((y - y0) / (FrostGap * 0.5f)) % 2) * FrostGap * 0.5f, y);
                    if (!Inside(p, a, b, c) || m_frost.Count > 40) continue;
                    var g = YsvUtil.Floor(YsveldFx.TriangleFrost, p);
                    if (g != null) m_frost.Add(g);
                }
            foreach (var cr in m_crystals) Show(YsveldFx.HermitCrystalFlash, cr.at);
        }

        static float Cross(Vector2 u, Vector2 v) { return u.x * v.y - u.y * v.x; }

        static bool Inside(Vector2 p, Vector2 a, Vector2 b, Vector2 c)
        {
            float d1 = Cross(b - a, p - a), d2 = Cross(c - b, p - b), d3 = Cross(a - c, p - c);
            bool neg = d1 < 0f || d2 < 0f || d3 < 0f, pos = d1 > 0f || d2 > 0f || d3 > 0f;
            return !(neg && pos);
        }

        void Update()
        {
            if (!Alive) { while (m_crystals.Count > 0) Melt(0); return; }
            for (int i = m_crystals.Count - 1; i >= 0; i--)
                if (m_crystals[i].go == null || !m_crystals[i].go.activeInHierarchy || Time.time - m_crystals[i].born > Life) Melt(i);
            if (!m_formed) return;
            m_tick -= Time.deltaTime;
            if (m_tick > 0f) return;
            m_tick = Tick;
            var hero = YsvUtil.LiveHero();
            if (hero == null || m_crystals.Count < Max) return;
            if (Inside(hero.transform.position, m_crystals[0].at, m_crystals[1].at, m_crystals[2].at))
            {
                YsvUtil.Rime(hero, Own, 1, true);
                Show(YsveldFx.TrianglePulse, hero.transform.position);
            }
        }
    }
}
