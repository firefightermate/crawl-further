using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Vhorrul
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Grand Chandelier, Hanging: it bobs on its chain, <see cref="Period"/> s low and <see cref="Period"/> s high (the
    /// chain's length and the size of its shadow show which). While high, blades can't reach it; shots can. It drops low
    /// to attack. Drip and Flare drips a ring of wax under it (radius <see cref="RingR"/>), then lights the whole ring.
    /// </summary>
    public class ChandelierHang : VhorrulBehaviour
    {
        public const float Period = 1.5f, RingR = 30f;
        public const int Drips = 8;
        public static exSpriteAnimClip IdleHigh, RunHigh;
        bool m_high;
        float m_t;

        protected override void OnEnable() { base.OnEnable(); m_high = false; m_t = Period; }

        void Update()
        {
            if (!Alive) return;
            m_t -= Time.deltaTime;
            if (InAttack) { if (m_high) SetHigh(false); m_t = Period; return; }
            if (m_t > 0f) return;
            m_t = Period;
            SetHigh(!m_high);
        }

        void SetHigh(bool on)
        {
            m_high = on;
            SetStance(on ? IdleHigh : null, on ? RunHigh : null);
        }

        public override bool BlockHeroHit(DamageInfo d) { return m_high && !IsShot(d); }

        static Vector2 RingPoint(int i) { float a = i * Mathf.PI * 2f / Drips; return new Vector2(Mathf.Cos(a) * RingR, Mathf.Sin(a) * RingR * 0.45f); }

        /// <summary>Clip event: hot wax drips round the ring over the next 1.4 s.</summary>
        public void VhDrip() { StopAllCoroutines(); StartCoroutine(DripRing(Me)); }

        IEnumerator DripRing(Vector2 centre)
        {
            var src = Own;
            for (int i = 0; i < Drips && Alive; i++)
            {
                int k = (i * 3) % Drips;   // round the ring out of order, like wax running off different candles
                if (VhorrulFx.Drip != null) FxFactory.SpawnOwned(VhorrulFx.Drip, centre + RingPoint(k), src);
                yield return new WaitForSeconds(1.4f / Drips);
            }
        }

        /// <summary>Clip event: every candle flares and the ring lights at once.</summary>
        public void VhFlare()
        {
            if (!Alive || VhorrulFx.RingFlare == null) return;
            for (int i = 0; i < Drips; i++) FxFactory.SpawnOwned(VhorrulFx.RingFlare, Me + RingPoint(i), Own);
        }
    }
}
