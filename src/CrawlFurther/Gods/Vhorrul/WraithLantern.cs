using UnityEngine;

namespace CrawlFurther.Content.Gods.Vhorrul
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Lantern Wraith, Soul in a Lantern: Take the Light swings the lantern in a cone (<see cref="Reach"/> px). A hero
    /// caught loses his soul flame for 4 s (the Soulless status: his hits deal 25 % less) and it burns in the lantern (the
    /// Full stance) while its soul orbs hit <see cref="OrbBonus"/> harder. He gets it back when time is up, or at once by
    /// stepping into any fire (<see cref="VhHeroWatch"/>).
    /// </summary>
    public class WraithLantern : VhorrulBehaviour
    {
        public const float Reach = 50f, HalfAngle = 35f, OrbBonus = 0.3f;
        public static exSpriteAnimClip IdleFull, RunFull;
        bool m_full;
        float m_t;

        protected override void OnEnable() { base.OnEnable(); m_full = false; }

        static PlayerStatusManager HeroStatus()
        {
            var h = ModUtil.Hero();
            var p = h != null ? h.GetComponent<Player>() : null;
            return p != null ? p.GetStatusManager() : null;
        }

        /// <summary>Clip event (the lantern swings through the cone).</summary>
        public void VhTakeLight()
        {
            var hero = ModUtil.Hero();
            if (!Alive || hero == null || VhorrulFx.Soulless == null) return;
            if (VhorrulFx.SoulCone != null) FxFactory.SpawnOwned(VhorrulFx.SoulCone, Me + new Vector2(Face.x >= 0f ? 20f : -20f, 22f), Own, AngleOf(Face));
            var to = HeroPos - Me;
            if (to.magnitude > Reach || Vector2.Angle(Face, to) > HalfAngle) return;
            var hp = hero.GetComponent<Player>();
            if (hp == null) return;
            hp.AddStatus(VhorrulFx.Soulless, Own, "vhsoulless");
            if (hero.GetComponent<VhHeroWatch>() == null) hero.AddComponent<VhHeroWatch>();
        }

        void Update()
        {
            m_t -= Time.deltaTime;
            if (m_t > 0f) return;
            m_t = 0.1f;
            var sm = HeroStatus();
            bool full = Alive && sm != null && VhorrulFx.Soulless != null && sm.GetHasStatusWithClass(VhorrulFx.Soulless.m_class);
            if (full == m_full) return;
            m_full = full;
            SetStance(full ? IdleFull : null, full ? RunFull : null);
        }

        public override void OnHitHero(DamageInfo d)
        {
            if (m_full && (From(d, VhorrulFx.LanternBlast) || From(d, VhorrulFx.LanternOrb))) d.m_amount += OrbBonus;
        }
    }
}
