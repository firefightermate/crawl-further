using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    using CrawlFurther.Util;

    /// <summary>The second half of a split Geode: 1.2x faster and its crystal inside takes +25% from the hero.</summary>
    public class GeodeHalfCore : YsveldBehaviour
    {
        bool m_fast;

        protected override void OnEnable() { base.OnEnable(); m_fast = false; }

        // the ice brain resets its speed when it wakes: set the half's own speed on its first frame
        void Update() { if (!m_fast && Frost != null) { m_fast = true; Frost.SetBaseSpeed(GeodeSplit.Speed); } }

        public override float HeroHitScale(DamageInfo d) { return GeodeSplit.Taken; }
    }
}
