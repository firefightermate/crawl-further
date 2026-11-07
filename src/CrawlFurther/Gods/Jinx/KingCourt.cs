using UnityEngine;

namespace CrawlFurther.Content.Gods.Jinx
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Card King, Hold Court with a Heavy Crown: for <see cref="GuardTime"/> s he holds the Diamonds card up: every hit
    /// the hero lands is blocked (so nothing knocks him back) and answered with a card thrown back, and he walks the court
    /// to the hero, slowly. Tell: the raised card and the glowing crown (the Court idle and run).
    /// </summary>
    public class KingCourt : JinxBehaviour
    {
        public const float GuardTime = 3f, AdvanceInput = 0.45f, RiposteGap = 0.2f;
        /// <summary>The stance while the court is held (set by the kit).</summary>
        public static exSpriteAnimClip CourtIdle, CourtRun;

        float m_until, m_nextRiposte;

        bool Guarding { get { return m_until > Time.time; } }

        protected override void OnEnable() { base.OnEnable(); m_until = 0f; }

        /// <summary>Clip event: the card goes up.</summary>
        public void ModJinxHoldCourt()
        {
            if (!Alive) return;
            m_until = Time.time + GuardTime;
            SetStance(CourtIdle, CourtRun);
        }

        void Update()
        {
            if (m_until <= 0f) return;
            if (!Alive || !Guarding)
            {
                m_until = 0f;
                Steer(null);
                SetStance(null, null);
                return;
            }
            Vector2 d = HeroPos - Me;
            Steer(d.sqrMagnitude > 18f * 18f && !InAttack ? d.normalized * AdvanceInput : Vector2.zero);
        }

        public override bool BlockHeroHit(DamageInfo d)
        {
            if (!Guarding) return false;
            if (Time.time >= m_nextRiposte && JinxFx.Riposte != null)
            {
                m_nextRiposte = Time.time + RiposteGap;
                Vector2 from = Me + new Vector2(12f * Side, 19f);
                FxFactory.SpawnOwned(JinxFx.Riposte, from, Own, AngleTo(from, HeroPos + new Vector2(0f, 6f)));
            }
            return true;
        }
    }
}
