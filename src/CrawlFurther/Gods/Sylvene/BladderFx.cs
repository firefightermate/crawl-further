using UnityEngine;

namespace CrawlFurther.Content.Gods.Sylvene
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>The Blight Bellows' gas bladder: it hops along the floor towards its target, puffs a small cloud at each of
    /// its <see cref="Bounces"/> bounces and bursts on the last landing.</summary>
    public class BladderFx : MonoBehaviour
    {
        public const int Bounces = 3;
        const float HopTime = 0.24f;
        Vector2 m_from, m_step;
        DamageSource m_src;
        int m_hop;
        float m_t;
        bool m_live;

        void OnEnable() { m_live = false; }

        /// <summary>Hop towards <paramref name="at"/>, owned by <paramref name="src"/>.</summary>
        public void Throw(Vector2 at, DamageSource src)
        {
            m_from = transform.position;
            var d = at - m_from;
            float hop = Mathf.Clamp(d.magnitude / (Bounces + 1), 10f, 22f);
            m_step = d.sqrMagnitude > 1f ? d.normalized * hop : Vector2.right * hop;
            m_src = src; m_hop = 0; m_t = 0f; m_live = true;
        }

        void Update()
        {
            if (!m_live) return;
            m_t += Time.deltaTime;
            float k = Mathf.Clamp01(m_t / HopTime);
            Vector2 a = m_from + m_step * m_hop, b = m_from + m_step * (m_hop + 1);
            if (!ModUtil.Clear(a, b)) b = a;   // a wall stops it where it is
            var p = Vector2.Lerp(a, b, k);
            transform.position = new Vector3(p.x, p.y, transform.position.z);
            if (k < 1f) return;
            m_hop++; m_t = 0f;
            if (m_hop <= Bounces)
            {
                if (SylveneFx.GasPuff != null) FxFactory.SpawnOwned(SylveneFx.GasPuff, p, m_src);
                if (b == a) { m_hop = Bounces + 1; Burst(p); }
                return;
            }
            Burst(p);
        }

        void Burst(Vector2 p)
        {
            m_live = false;
            if (SylveneFx.BladderBurst != null) FxFactory.SpawnOwned(SylveneFx.BladderBurst, p, m_src);
            if (!SystemMain.GetDeloadInProgress()) SystemPool.Despawn(gameObject);
        }
    }
}
