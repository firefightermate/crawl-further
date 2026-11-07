using UnityEngine;

namespace CrawlFurther.Content.Gods.Umbrael
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// The Twinned, Crossed Echo: Swap trades places with the hero; for a moment after, its cuts echo in both places, where
    /// it stood and where he stood. Tell: two afterimages, one at each spot.
    /// </summary>
    public class TwinnedCrossed : UmbraelBehaviour
    {
        public const float Window = 1.4f;
        Vector2 m_offset;
        float m_until = -99f;

        protected override void OnEnable() { base.OnEnable(); m_until = -99f; }

        /// <summary>Clip event: the swap itself.</summary>
        public void ModUmbTwinSwap()
        {
            var h = ModUtil.Hero();
            if (h == null) return;
            Vector2 stood = Me, his = h.transform.position;
            Monster.SwapWithHero(UmbraelFx.SwapFlash);
            m_offset = stood - his;      // from where it now stands to where it stood
            m_until = Time.time + Window;
        }

        public override void PlanEcho(EchoPlan plan)
        {
            if (Time.time > m_until || m_offset.sqrMagnitude < 4f) return;
            int n = plan.sites.Count;
            for (int i = 0; i < n; i++) plan.sites.Add(plan.sites[i] + m_offset);
            AfterimageFx.Spawn(Sprite, (Vector3)(Me + m_offset) + new Vector3(0f, 0f, transform.position.z), plan.delay + 0.15f);
            if (UmbraelFx.EchoMark != null) SystemPool.Spawn(UmbraelFx.EchoMark, Me + m_offset);
        }
    }
}
