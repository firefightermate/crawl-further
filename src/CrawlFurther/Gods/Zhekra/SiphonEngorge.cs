using UnityEngine;

namespace CrawlFurther.Content.Gods.Zhekra
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Blood Siphon, Engorge: each stab that lands fills its belly a stage (three). Full, it flies at
    /// <see cref="FullSpeed"/>x and takes <see cref="FullDamage"/>x. Killed full, it bursts and heals every Zhekra within
    /// <see cref="BurstRadius"/> px by <see cref="BurstHeal"/>. Tell: the belly swells red (its stance).
    /// </summary>
    public class SiphonEngorge : ZhkBehaviour
    {
        public const int Full = 3;
        public const float FullSpeed = 0.8f, FullDamage = 1.25f, BurstRadius = 50f, BurstHeal = 1f;
        /// <summary>Idle and run with the belly at 0-3 (set by the kit).</summary>
        public static exSpriteAnimClip[] Idles, Runs;

        int m_stage;

        protected override void OnEnable() { base.OnEnable(); Fill(0); }

        void Fill(int n)
        {
            m_stage = Mathf.Clamp(n, 0, Full);
            Stage(Idles, Runs, m_stage);
            SpeedScale(m_stage >= Full ? FullSpeed : 1f);
        }

        protected override void OnHeroContact(DamageInfo d, string effect)
        {
            if (effect == "ModZhkStab" || effect == "ModZhkFeedStab") Fill(m_stage + 1);
        }

        public override float HeroHitScale(DamageInfo d) { return m_stage >= Full ? FullDamage : 1f; }

        void OnKilled(DamageInfo d)
        {
            if (m_stage < Full) return;
            m_stage = 0;
            if (ZhekraFx.Mend != null) SystemPool.Spawn(ZhekraFx.Mend, Me);
            foreach (var k in Kin(Me, BurstRadius)) k.Mend(BurstHeal);
        }
    }
}
