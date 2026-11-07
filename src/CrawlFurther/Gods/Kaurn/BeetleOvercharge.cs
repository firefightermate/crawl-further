namespace CrawlFurther.Content.Gods.Kaurn
{
    /// <summary>
    /// Spark Beetle's Overcharge: with 3 sparks stored the sparks on its shell burn white, and its next roll is the big ball
    /// (twice the size, a sure stun) that spends them instead of firing them.
    /// </summary>
    public class BeetleOvercharge : KaurnBehaviour
    {
        public static exSpriteAnimClip ChargedIdle, ChargedRun, RushBig;
        bool m_full;

        protected override void OnEnable() { base.OnEnable(); m_full = false; SetSpecialClip(null); }

        void Update()
        {
            bool full = Unit.pips >= KaurnUnit.MaxPips;
            if (full == m_full || InAttack) return;
            m_full = full;
            SetStance(full ? ChargedIdle : null, full ? ChargedRun : null);
            SetSpecialClip(full ? RushBig : null);
        }

        /// <summary>Clip event (the big roll): the stored sparks go into the ball.</summary>
        public void KrnSpendSparks() { Unit.pips = 0; }
    }
}
