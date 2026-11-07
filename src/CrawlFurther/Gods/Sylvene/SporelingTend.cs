using UnityEngine;

namespace CrawlFurther.Content.Gods.Sylvene
{
    using CrawlFurther.Monsters;

    /// <summary>Sporeling, Tend: seeds within <see cref="Range"/> px of it ripen twice as fast (1.2 s). Tell: green motes
    /// drifting down from its cap onto each seed it tends.</summary>
    public class SporelingTend : SylveneBehaviour
    {
        public const float Range = 20f, Pulse = 0.4f;
        float m_next;

        protected override void OnEnable() { base.OnEnable(); m_next = 0f; }

        void Update()
        {
            if (!Alive || Time.time < m_next) return;
            m_next = Time.time + Pulse;
            foreach (var s in SeedFx.All)
            {
                if (s == null || s.Ripe || !Near(s.Pos, Me, Range)) continue;
                s.Tend(Pulse + 0.1f);
                if (SylveneFx.TendMote != null) SystemPool.Spawn(SylveneFx.TendMote, s.Pos);
            }
        }
    }
}
