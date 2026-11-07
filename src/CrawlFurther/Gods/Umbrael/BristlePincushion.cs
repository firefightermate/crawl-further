using UnityEngine;

namespace CrawlFurther.Content.Gods.Umbrael
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Bristleback, Pincushion: the hero's shots that hit it stick in its back (up to 3) and go out with its next Nail
    /// Lob, one extra nail each. Tell: his bolts sticking out of its back.
    /// </summary>
    public class BristlePincushion : UmbraelBehaviour
    {
        public const int Max = 3;
        int m_stuck;
        float m_lobAt = -99f;

        protected override void OnEnable() { base.OnEnable(); Set(0); }
        protected override void OnDisable() { base.OnDisable(); Set(0); }

        void Set(int n)
        {
            m_stuck = n;
            ModInd.Count(gameObject, UmbraelFx.StuckInd, Alive ? n : 0);
        }

        public override void OnHeroHit(DamageInfo d)
        {
            if (m_stuck < Max && IsShot(d)) Set(m_stuck + 1);
        }

        public override void OnAttackSpawned(GameObject fx, GameObject template)
        {
            if (template != UmbraelFx.Quill || m_stuck == 0 || Time.time - m_lobAt < 0.3f) return;
            m_lobAt = Time.time;
            float a = AngleTo(Me, HeroPos);
            for (int i = 0; i < m_stuck; i++)
            {
                float off = (i == 0 ? 11f : i == 1 ? -11f : 33f);
                FxFactory.SpawnOwned(UmbraelFx.Quill, fx.transform.position, Own, a + off);
            }
            Set(0);
        }
    }
}
