using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Cerberus, Pincer: Converging Breath sends three cones of grave gas at -40, 0 and +40 degrees; the outer heads breathe
    /// first and their cones sweep inward over <see cref="Sweep"/> s until all three meet ahead, so the way out is back.
    /// Tell: the outer heads glowing first.
    /// </summary>
    public class CerberusBreath : OssBehaviour
    {
        public const float Outer = 40f, Sweep = 1f, Life = 1.2f;
        readonly GameObject[] m_hit = new GameObject[3], m_art = new GameObject[3];
        float m_t, m_base;
        bool m_on;

        protected override void OnEnable() { base.OnEnable(); m_on = false; }
        protected override void OnDisable() { base.OnDisable(); End(); }

        Vector2 Mouth { get { return Me + new Vector2(Side * 25f, 17f); } }

        void Open(int i)
        {
            if (OssivarFx.GasConeHit != null) m_hit[i] = FxFactory.SpawnOwned(OssivarFx.GasConeHit, Mouth, Own);
            if (OssivarFx.GasConeArt != null) m_art[i] = SystemPool.Spawn(OssivarFx.GasConeArt, Mouth);
        }

        /// <summary>Clip event (Breath frame 2): the outer heads breathe.</summary>
        public void OssBreathOuter()
        {
            if (!Alive) return;
            m_on = true; m_t = 0f; m_base = AngleOf(Face);
            Open(0); Open(2);
            Place();
        }

        /// <summary>Clip event (Breath frame 3): the middle head joins.</summary>
        public void OssBreathMiddle() { if (m_on) { Open(1); Place(); } }

        /// <summary>Clip event (Breath frame 9).</summary>
        public void OssBreathEnd() { End(); }

        void End()
        {
            m_on = false;
            for (int i = 0; i < 3; i++)
            {
                if (m_hit[i] != null && m_hit[i].activeInHierarchy) SystemPool.Despawn(m_hit[i]);
                if (m_art[i] != null && m_art[i].activeInHierarchy) SystemPool.Despawn(m_art[i]);
                m_hit[i] = null; m_art[i] = null;
            }
        }

        void Place()
        {
            float k = Mathf.Clamp01(m_t / Sweep);
            for (int i = 0; i < 3; i++)
            {
                float a = m_base + (i - 1) * Mathf.Lerp(Outer, 4f, k);
                foreach (var go in new[] { m_hit[i], m_art[i] })
                {
                    if (go == null) continue;
                    var p = Mouth;
                    go.transform.position = new Vector3(p.x, p.y, go.transform.position.z);
                    go.transform.rotation = Quaternion.Euler(0f, 0f, a);
                }
            }
        }

        void Update()
        {
            if (!m_on) return;
            if (!Alive || !InAttack || m_t > Life) { End(); return; }
            m_t += Time.deltaTime;
            Place();
        }
    }
}
