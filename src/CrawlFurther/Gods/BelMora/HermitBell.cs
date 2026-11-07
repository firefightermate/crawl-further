using UnityEngine;

namespace CrawlFurther.Content.Gods.BelMora
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Bell Hermit. Bell Down: for <see cref="Guard"/> s inside its bell it takes a third of the damage and every hit rings
    /// the bell (FxPeal). Bellful of Brine: walking through brine scoops a load into its bell (one at most); Bell Down
    /// pours it out as a brine pool round itself. Tell: water sloshing at the bell's lip, dripping as it walks (Full).
    /// </summary>
    public class HermitBell : BelBehaviour
    {
        public const float Guard = 1.5f, Taken = 1f / 3f, PealGap = 0.3f;
        /// <summary>The idle and run with a bellful of brine (set by the kit).</summary>
        public static exSpriteAnimClip FullIdle, FullRun;

        float m_guard, m_gap, m_scan;
        bool m_full;

        protected override void OnEnable() { base.OnEnable(); m_guard = 0f; m_gap = 0f; m_full = false; }

        /// <summary>Clip event: the bell comes down.</summary>
        public void BelShellOn()
        {
            m_guard = Guard;
            Ring();
            if (!m_full) return;
            SetFull(false);
            BelTide.Well(Feet, Own);
        }

        /// <summary>Clip event: it comes back out.</summary>
        public void BelShellOff() { m_guard = 0f; }

        public override float HeroHitScale(DamageInfo d) { return m_guard > 0f ? Taken : 1f; }
        public override void OnHeroHit(DamageInfo d) { if (m_guard > 0f) Ring(); }

        void Ring()
        {
            if (BelMoraFx.Peal == null || m_gap > 0f) return;
            m_gap = PealGap;
            FxFactory.SpawnOwned(BelMoraFx.Peal, Feet, Own);
        }

        void SetFull(bool full)
        {
            m_full = full;
            SetStance(full ? FullIdle : null, full ? FullRun : null);
        }

        void Update()
        {
            if (m_gap > 0f) m_gap -= Time.deltaTime;
            if (m_guard > 0f) m_guard -= Time.deltaTime;
            if (!Alive || m_full) return;
            m_scan -= Time.deltaTime;
            if (m_scan > 0f) return;
            m_scan = 0.2f;
            if (BelWater.InBrine(Feet)) SetFull(true);
        }
    }
}
