using UnityEngine;

namespace CrawlFurther.Content.Gods.BelMora
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Anemone Colossus, Open in the Tide: standing in brine its garden opens and stings all round it (a field
    /// <see cref="Field"/> px round, every <see cref="Every"/> s); on dry floor the anemones close. Its Budding flicks two
    /// anemone buds by the hero that root and sting for 5 s. Tell: the anemones open and waving, or shut into buds.
    /// </summary>
    public class ColossusGarden : BelBehaviour
    {
        public const float Field = 24f, Every = 0.6f;
        /// <summary>The open garden stance (set by the kit).</summary>
        public static exSpriteAnimClip OpenIdle, OpenRun;

        bool m_open;
        float m_scan, m_pulse;

        protected override void OnEnable() { base.OnEnable(); m_open = false; m_pulse = 0f; }

        void Update()
        {
            if (!Alive) return;
            m_scan -= Time.deltaTime;
            if (m_scan <= 0f)
            {
                m_scan = 0.2f;
                bool open = BelWater.InBrine(Feet);
                if (open != m_open)
                {
                    m_open = open;
                    SetStance(open ? OpenIdle : null, open ? OpenRun : null);
                    m_pulse = 0f;
                }
            }
            if (!m_open || BelMoraFx.GardenPulse == null) return;
            m_pulse -= Time.deltaTime;
            if (m_pulse > 0f) return;
            m_pulse = Every;
            FxFactory.SpawnOwned(BelMoraFx.GardenPulse, Feet, Own);
        }
    }
}
