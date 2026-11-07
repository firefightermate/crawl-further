using UnityEngine;

namespace CrawlFurther.Content.Gods.Jinx
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// House of Cards, Collapse: every hit from the hero knocks a tier off (3 to 0). Each lost tier makes it
    /// <see cref="SpeedPerTier"/> faster; at none left it is a whirlwind of loose cards that cuts all round it. Tell: its
    /// height is its tier count. Also casts Card Storm (six cards circle it, then fly at the hero one by one).
    /// Basics 0-3: Topple (3 tiers), Topple2, Topple1, WhirlSlash.
    /// </summary>
    public class HouseTiers : JinxBehaviour
    {
        public const int MaxTiers = 3, StormCards = 6;
        public const float SpeedPerTier = 0.15f, StormLaunch = 2.5f, StormGap = 0.18f;
        /// <summary>Per tiers left (0..2): idle, run and Storm clips (set by the kit; tier 3 is the body's own).</summary>
        public static exSpriteAnimClip[] TierIdle, TierRun, TierStorm;

        int m_tiers = MaxTiers;

        protected override void OnEnable() { base.OnEnable(); m_tiers = MaxTiers; }

        public override void OnHeroHit(DamageInfo d)
        {
            if (m_tiers <= 0) return;
            m_tiers--;
            if (JinxFx.TierFall != null) SystemPool.Spawn(JinxFx.TierFall, Me);
            bool full = m_tiers == MaxTiers;
            SetStance(full || TierIdle == null ? null : TierIdle[m_tiers], full || TierRun == null ? null : TierRun[m_tiers]);
            SetSpecialClip(full || TierStorm == null ? null : TierStorm[m_tiers]);
            NextBasic(MaxTiers - m_tiers);
            SpeedScale(1f + SpeedPerTier * (MaxTiers - m_tiers));
        }

        /// <summary>Clip event: the storm cards peel off and circle it.</summary>
        public void ModJinxCardStorm()
        {
            if (JinxFx.OrbitCard == null || !Alive) return;
            float start = Random.Range(0f, 360f);
            for (int i = 0; i < StormCards; i++)
            {
                var go = FxFactory.SpawnOwned(JinxFx.OrbitCard, Me + new Vector2(0f, JinxOrbitCardFx.Height), Own);
                if (go == null) continue;
                var o = go.GetComponent<JinxOrbitCardFx>() ?? go.AddComponent<JinxOrbitCardFx>();
                o.Bind(transform, Hp, start + i * 360f / StormCards, StormLaunch + i * StormGap);
            }
        }
    }
}
