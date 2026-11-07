using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Coffin Bearer. Whirl spins the coffin on its chain for <see cref="WhirlTime"/> s, the radius growing from 14 to 34 px,
    /// walking at half speed toward the hero; up to three hits, 0.5 s apart. Then it staggers, dizzy, for 0.8 s.
    /// Let It Fly: pressing the special again mid-whirl lets go: the coffin flies 60 px on its chain in the facing direction
    /// and is yanked back, and the stagger is skipped (a bot lets go when the hero is in that range ahead). Tell: the chain
    /// at full stretch, the lid rattling.
    /// </summary>
    public class BearerWhirl : OssBehaviour
    {
        public const float WhirlTime = 2f, R0 = 14f, R1 = 34f, HitEvery = 0.5f, Walk = 26f, Dizzy = 0.8f, Fling = 60f;
        /// <summary>Set by the kit.</summary>
        public static exSpriteAnimClip FlingClip, DizzyClip;
        bool m_whirling, m_flung;
        float m_t, m_nextHit;
        int m_hits;

        protected override void OnEnable() { base.OnEnable(); m_whirling = false; }

        /// <summary>Clip event (Whirl start).</summary>
        public void OssWhirlOn() { m_whirling = true; m_flung = false; m_t = 0f; m_nextHit = HitEvery; m_hits = 0; }

        /// <summary>Clip event (Whirl end): dizzy unless it let go.</summary>
        public void OssWhirlEnd()
        {
            if (!m_whirling) return;
            m_whirling = false;
            if (!m_flung) Hold(DizzyClip, Dizzy);
        }

        bool WantsToLetGo()
        {
            var pd = Body != null ? Body.GetPlayerData() : null;
            if (pd == null) return false;
            if (!pd.IsBot && pd.GetInputDownBack()) return true;
            if (!pd.IsBot || m_t < 0.6f || Hero == null) return false;
            Vector2 d = HeroPos - Me;
            return d.magnitude > 36f && d.magnitude < Fling + 12f && Vector2.Dot(d.normalized, Face) > 0.8f;
        }

        void Update()
        {
            if (!m_whirling) return;
            if (!Alive || !InAttack) { m_whirling = false; return; }
            m_t += Time.deltaTime;
            if (Hero != null)
            {
                Vector2 d = HeroPos - Me;
                if (d.sqrMagnitude > 64f) Slide(d.normalized * Walk * Time.deltaTime);
                Monster.FaceHero();
            }
            if (m_hits < 3 && m_t >= m_nextHit && OssivarFx.WhirlHit != null)
            {
                m_hits++; m_nextHit += HitEvery;
                float r = Mathf.Lerp(R0, R1, m_t / WhirlTime);
                var go = FxFactory.SpawnOwned(OssivarFx.WhirlHit, Me + new Vector2(0f, 6f), Own);
                if (go != null) Strike.HitBox(go, r * 2f + 10f, r * 1.4f + 8f);
            }
            if (m_t > 0.3f && WantsToLetGo()) LetGo();
        }

        void LetGo()
        {
            m_whirling = false; m_flung = true;
            Monster.FaceHero();
            Play(FlingClip);
        }

        /// <summary>Clip event (Fling frame 3): the coffin at full stretch.</summary>
        public void OssFlingHit()
        {
            if (!Alive || OssivarFx.FlingHit == null) return;
            Vector2 tip = ModUtil.SafePoint(Me, Me + new Vector2(Side * Fling, 0f), 4f) + new Vector2(0f, 6f);
            FxFactory.SpawnOwned(OssivarFx.FlingHit, tip, Own);
        }
    }
}
