using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.BelMora
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Jelly Siren. Trailing Tentacles: her tentacles trail <see cref="Trail"/> px behind her along the path she took;
    /// crossing them stings (slows), at most once every <see cref="Gap"/> s. Jet Pulse: three pulses, each jets her
    /// <see cref="Jet"/> px round the hero in an arc and sheds a sting ring where she stops. Tell: glowing lines behind
    /// her that fade at the far end.
    /// </summary>
    public class JellyTrail : BelBehaviour
    {
        public const float Trail = 40f, Gap = 0.6f, Touch = 5f, Jet = 30f, JetTime = 0.12f, Height = 4f;

        readonly List<Vector2> m_path = new List<Vector2>();
        readonly BelLine[] m_segs = { new BelLine(), new BelLine(), new BelLine(), new BelLine() };
        float m_gap;
        int m_turn = 1;

        protected override void OnEnable() { base.OnEnable(); m_path.Clear(); m_gap = 0f; }
        protected override void OnDisable() { base.OnDisable(); foreach (var s in m_segs) s.Clear(); }

        void Update()
        {
            if (!Alive) { foreach (var s in m_segs) s.Clear(); return; }
            if (m_gap > 0f) m_gap -= Time.deltaTime;
            Vector2 me = Me + new Vector2(0f, Height);
            if (m_path.Count == 0 || (m_path[m_path.Count - 1] - me).sqrMagnitude > 9f) m_path.Add(me);
            // keep only the last 40 px of path
            float len = 0f;
            int keep = m_path.Count - 1;
            for (int i = m_path.Count - 1; i > 0; i--)
            {
                len += (m_path[i] - m_path[i - 1]).magnitude;
                keep = i - 1;
                if (len >= Trail) break;
            }
            if (keep > 0) m_path.RemoveRange(0, keep);
            Draw();
            Sting();
        }

        // four segments along the trail behind her (the last one fading)
        void Draw()
        {
            for (int k = 0; k < m_segs.Length; k++)
            {
                int i0 = Mathf.FloorToInt((m_path.Count - 1) * (1f - (k + 1f) / m_segs.Length));
                int i1 = Mathf.FloorToInt((m_path.Count - 1) * (1f - (float)k / m_segs.Length));
                if (m_path.Count < 2 || i0 == i1) { m_segs[k].Clear(); continue; }
                m_segs[k].Lay(BelMoraFx.TrailSeg, m_path[i0], m_path[i1], 10f, rotate: true);
            }
        }

        void Sting()
        {
            var hero = ModUtil.Hero();
            if (m_gap > 0f || hero == null || m_path.Count < 2 || BelMoraFx.TrailSting == null) return;
            Vector2 hp = (Vector2)hero.transform.position + new Vector2(0f, Height);
            for (int i = 1; i < m_path.Count - 1; i++)
            {
                var a = m_path[i - 1]; var b = m_path[i];
                var ab = b - a;
                float t = Mathf.Clamp01(Vector2.Dot(hp - a, ab) / Mathf.Max(0.01f, ab.sqrMagnitude));
                if ((a + ab * t - hp).sqrMagnitude > Touch * Touch) continue;
                m_gap = Gap;
                FxFactory.SpawnOwned(BelMoraFx.TrailSting, hero.transform.position, Own);
                return;
            }
        }

        /// <summary>Clip event (Jet, each pulse): she jets 30 px round the hero and sheds a sting ring where she stops.</summary>
        public void BelJet()
        {
            if (!Alive || !gameObject.activeInHierarchy) return;
            StartCoroutine(JetRun());
        }

        IEnumerator JetRun()
        {
            Vector2 hp = HeroPos;
            var r = Me - hp;
            if (r.sqrMagnitude < 1f) r = -Face;
            float rad = Mathf.Clamp(r.magnitude, 16f, 70f);
            float a0 = Mathf.Atan2(r.y, r.x);
            float da = (Jet / rad) * m_turn;
            float t = 0f;
            while (t < JetTime && Alive)
            {
                t += Time.deltaTime;
                float a = a0 + da * Mathf.Clamp01(t / JetTime);
                var to = hp + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * rad;
                ModUtil.Teleport(gameObject, ModUtil.SafePoint(Me, to, 3f));
                yield return null;
            }
            if (Random.value < 0.3f) m_turn = -m_turn;
            if (Alive && BelMoraFx.JetRing != null) FxFactory.SpawnOwned(BelMoraFx.JetRing, Feet, Own);
        }
    }
}
