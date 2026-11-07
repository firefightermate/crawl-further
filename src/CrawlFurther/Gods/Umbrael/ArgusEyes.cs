using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Umbrael
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Argus Moth, Eye-Catching: the hero's shots that pass within 30 px of it veer into its wings and hit it for half
    /// damage, shielding its kin. Tell: every painted eye snaps to the shot and glows (its Catch flourish).
    /// </summary>
    public class ArgusEyes : UmbraelBehaviour
    {
        public const float Range = 30f, WingY = 18f;
        /// <summary>The eyes-catching flourish (set by the kit).</summary>
        public static exSpriteAnimClip CatchClip;
        readonly List<ParticleMotion> m_near = new List<ParticleMotion>();
        readonly HashSet<GameObject> m_caught = new HashSet<GameObject>();

        protected override void OnEnable() { base.OnEnable(); m_caught.Clear(); }

        void Update()
        {
            if (!Alive) return;
            var wings = Me + new Vector2(0f, WingY);
            HeroShots.Near(wings, Range, m_near);
            foreach (var pm in m_near)
            {
                if (m_caught.Contains(pm.gameObject)) continue;
                m_caught.Add(pm.gameObject);
                HeroShots.Turn(pm, wings - (Vector2)pm.transform.position);
                Flourish(CatchClip);
                if (UmbraelFx.ArgusCatch != null) SystemPool.Spawn(UmbraelFx.ArgusCatch, Me);
            }
            if (m_caught.Count > 16) m_caught.RemoveWhere(g => g == null || !g.activeInHierarchy);
        }

        public override float HeroHitScale(DamageInfo d)
        {
            var src = d.m_source.m_source;
            return src != null && m_caught.Contains(src) ? 0.5f : 1f;
        }

        public override void OnHeroHit(DamageInfo d)
        {
            var src = d.m_source.m_source;
            if (src != null) m_caught.Remove(src);
        }
    }
}
