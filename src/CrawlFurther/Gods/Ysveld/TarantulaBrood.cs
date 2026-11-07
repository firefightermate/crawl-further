using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    /// <summary>
    /// Hoarfrost Tarantula, Brood on Its Back: like a wolf spider it carries its young. Every 3 damage it takes shakes a
    /// Broodling off its back to run at the hero, three at most. Tell: the little spiders in its fur, fewer each time
    /// (Idle/Run carry three, Idle2/Run2 two, Idle1/Run1 one, Idle0/Run0 none).
    /// </summary>
    public class TarantulaBrood : YsveldBehaviour
    {
        public const float Per = 3f;
        public const int Brood = 3;
        public static exSpriteAnimClip[] BroodIdle, BroodRun;     // index = Broodlings left (0-2)
        float m_taken;
        int m_left;

        protected override void OnEnable() { base.OnEnable(); m_taken = 0f; m_left = Brood; }

        public override void OnHeroHit(DamageInfo d) { Count(d.m_amount); }

        /// <summary>Health's damage message: hits from anything count, not only the hero's.</summary>
        void OnDamaged(DamageInfo d)
        {
            if (d == null || d.m_source == null || d.m_source.m_sourceOwnerPlayer == CrawlFurther.Util.ModUtil.Hero()) return;
            Count(d.m_amount);
        }

        void Count(float amount)
        {
            if (m_left <= 0 || !Alive) return;
            m_taken += amount;
            while (m_taken >= Per && m_left > 0)
            {
                m_taken -= Per;
                m_left--;
                Spawn(YsveldFx.BroodShake, Me + new Vector2(-6f * Side, 4f));
                if (BroodIdle != null && BroodRun != null) SetStance(BroodIdle[m_left], BroodRun[m_left]);
            }
        }
    }
}
