using UnityEngine;

namespace CrawlFurther.Content.Gods.Zhekra
{
    using CrawlFurther.Util;

    /// <summary>
    /// Acid Grub, Gorge: a bite that lands on a hero already coated in acid makes it grow: +<see cref="Growth"/> health
    /// and max health, up to <see cref="MaxFeeds"/> times. Tell: it gets visibly fatter, one more segment per feed (its
    /// stance, bite and spit all change to the bigger body). Basic n is the bite of the grub after n feeds.
    /// </summary>
    public class GrubGorge : ZhkBehaviour
    {
        public const int MaxFeeds = 3;
        public const float Growth = 0.3f;
        /// <summary>Idle, run and spit of the grub after 0-3 feeds (set by the kit).</summary>
        public static exSpriteAnimClip[] Idles, Runs, Spits;

        int m_feeds;
        bool m_wasCorroded;

        // a pooled body's max health is worked out again from its base when it is inhabited
        protected override void OnEnable() { base.OnEnable(); m_feeds = 0; }

        // the bite's own acid lands in the same hit, so judge the coat by the frame before
        void Update() { m_wasCorroded = HeroCorroded(); }

        protected override void OnHeroContact(DamageInfo d, string effect)
        {
            if (effect != "ModZhkGrubBite" || !m_wasCorroded || m_feeds >= MaxFeeds) return;
            m_feeds++;
            R.Set(Hp, "m_healthMaxFinal", Hp.GetHealthMax() + Growth);
            Hp.Heal(Growth);
            CrawlFurther.Monsters.ModInd.Heal(gameObject);
            Stage(Idles, Runs, m_feeds);
            NextBasic(m_feeds);
            if (Spits != null && m_feeds < Spits.Length) SetSpecialClip(Spits[m_feeds]);
        }
    }
}
